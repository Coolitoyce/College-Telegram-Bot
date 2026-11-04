"""
Contribution review in the admin group.

Every file a student contributes is copied to the admin group as a "card" with
✅ Approve / ❌ Reject buttons. Approve opens the course/type picker and saves the
file straight into the database (no re-uploading or captions needed).
When a student finishes sending several files, a batch card lets you approve or
reject all of them at once. Link contributions are approved to a course and the
bot asks for a title per link. The contributor is notified either way.
"""
from html import escape
from asyncio import sleep
from telebot.types import CallbackQuery, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton, Message, LinkPreviewOptions
import logging
import database
from config import bot, ADMIN_GROUP, MATERIAL_TYPES, UserState, user_states, log_to_group
from handlers.admin import isadmin
from handlers import picker
#===========
logger = logging.getLogger("coolig_bot")

REJECT_REASONS = { # code: (admin label, message to the student)
    "dup": ("Duplicate", "الملف موجود بالفعل في البوت."),
    "irr": ("Irrelevant / wrong", "المحتوى غير مناسب أو مش تبع مواد الكلية."),
    "qual": ("Low quality", "جودة الملف ضعيفة أو غير واضحة."),
    "none": ("No reason", None),
}


#===========
# Helpers
def user_label(user) -> str:
    return f"@{user.username}" if user.username else user.full_name


def _status_pending() -> str:
    return "⏳ <i>Pending review</i>"


def file_card_text(c: dict, status_line: str) -> str:
    batch = f" · batch #{c['batch_id']}" if c.get("batch_id") else ""
    return (
        f"📥 <b>Contribution #{c['id']}</b>{batch}\n"
        f"👤 {escape(c['user_label'] or '')} · <code>{c['user_id']}</code>\n"
        f"📄 {escape(c['file_name'] or '')}\n\n"
        f"{status_line}"
    )


def link_card_text(c: dict, status_line: str) -> str:
    links = "\n".join(f"{i}. {escape(url)}" for i, url in enumerate(c["urls"].split("\n"), 1))
    return (
        f"🔗 <b>Link contribution #{c['id']}</b>\n"
        f"👤 {escape(c['user_label'] or '')} · <code>{c['user_id']}</code>\n\n"
        f"{links}\n\n"
        f"{status_line}"
    )


def batch_card_text(batch: dict, files: int, status_line: str) -> str:
    return (
        f"📦 <b>Batch #{batch['id']}</b> — {files} file(s)\n"
        f"👤 {escape(batch['user_label'] or '')} · <code>{batch['user_id']}</code>\n\n"
        f"{status_line}"
    )


def review_markup(token: str) -> InlineKeyboardMarkup:
    """Approve/Reject buttons for a contribution (c<ID>) or batch (b<ID>)"""
    all_ = " all pending" if token.startswith("b") else ""
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(f"✅ Approve{all_}", callback_data=f"pk:{token}:y"),
        InlineKeyboardButton(f"❌ Reject{all_}", callback_data=f"rv:r:{token}"),
    )
    return markup


def reject_markup(token: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📍 Choose a reason (sent to the student)", callback_data="noop"))
    for code, (label, _) in REJECT_REASONS.items():
        markup.row(InlineKeyboardButton(label, callback_data=f"rv:rr:{token}:{code}"))
    markup.row(InlineKeyboardButton("🔙 Back", callback_data=f"rv:back:{token}"))
    return markup


async def _edit_card(chat_id: int, message_id: int, text: str, is_media: bool, markup=None):
    try:
        if is_media:
            await bot.edit_message_caption(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)
        else:
            await bot.edit_message_text(
                text, chat_id, message_id, parse_mode="HTML", reply_markup=markup,
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
    except Exception as e:
        logger.warning(f"Failed to edit review card {chat_id}/{message_id}: {e}")


async def _notify(user_id: int, text: str):
    try:
        await bot.send_message(user_id, text, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Couldn't notify user {user_id}: {e}")


def _target_label(course: dict, material_type: str | None) -> str:
    type_label = f" · {MATERIAL_TYPES.get(material_type, material_type)}" if material_type else ""
    return f"<b>{escape(course['name'])}</b>{type_label}"


#===========
# Posting contributions (called from handlers/contribute.py)
async def post_file_contribution(message: Message, batch_id: int | None):
    """Saves a contributed file and copies it to the admin group with review buttons"""
    if message.content_type == "photo":
        media, file_id, file_name = "photo", message.photo[-1].file_id, message.caption or "Photo"
    elif message.content_type == "video":
        media, file_id = "video", message.video.file_id
        file_name = message.video.file_name or message.caption or "Video"
    else:
        media, file_id, file_name = "document", message.document.file_id, message.document.file_name or "File"

    label = user_label(message.from_user)
    cid = await database.add_contribution(
        message.from_user.id, label, "file", batch_id=batch_id, file_id=file_id, media=media, file_name=file_name[:200]
    )
    contribution = await database.get_contribution(cid)
    sent = await bot.copy_message(
        ADMIN_GROUP, message.chat.id, message.id,
        caption=file_card_text(contribution, _status_pending()),
        parse_mode="HTML",
        reply_markup=review_markup(f"c{cid}")
    )
    await database.set_contribution_card(cid, ADMIN_GROUP, sent.message_id)
    return cid


async def post_link_contribution(message: Message, urls: list[str]):
    """Saves a link contribution and posts it to the admin group with review buttons"""
    cid = await database.add_contribution(
        message.from_user.id, user_label(message.from_user), "link", urls="\n".join(urls)
    )
    contribution = await database.get_contribution(cid)
    sent = await bot.send_message(
        ADMIN_GROUP,
        link_card_text(contribution, _status_pending()),
        parse_mode="HTML",
        reply_markup=review_markup(f"c{cid}"),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
    await database.set_contribution_card(cid, ADMIN_GROUP, sent.message_id)
    return cid


async def post_batch_card(batch_id: int):
    """Posts a summary card when a student finishes sending files"""
    batch = await database.get_batch(batch_id)
    files = await database.get_batch_contributions(batch_id)
    if not batch or not files:
        return
    markup = review_markup(f"b{batch_id}") if len(files) > 1 else None
    sent = await bot.send_message(
        ADMIN_GROUP, batch_card_text(batch, len(files), _status_pending()), parse_mode="HTML", reply_markup=markup
    )
    await database.update_batch(batch_id, card_chat_id=ADMIN_GROUP, card_message_id=sent.message_id)


async def post_description(batch_id: int, message: Message):
    """Saves a batch description and posts it under the batch card"""
    await database.update_batch(batch_id, description=message.text)
    batch = await database.get_batch(batch_id)
    text = (
        f"📝 <b>Description for batch #{batch_id}</b> from {escape(batch['user_label'] or '')}:\n"
        f"<blockquote>{escape(message.text)}</blockquote>"
    )
    try:
        await bot.send_message(ADMIN_GROUP, text, parse_mode="HTML", reply_to_message_id=batch["card_message_id"])
    except Exception:
        await bot.send_message(ADMIN_GROUP, text, parse_mode="HTML")


#===========
# Approving
async def _approve_file(c: dict, course: dict, material_type: str, admin) -> int | None:
    """Adds one file contribution as a material and updates its card. Returns material ID."""
    if not await database.set_contribution_status(c["id"], "approved", admin.id):
        return None # already reviewed
    try:
        material_id = await database.add_material(course["id"], c["file_name"], material_type, c["file_id"], c["media"])
    except Exception:
        logger.exception(f"Failed to add material from contribution {c['id']}")
        await database._execute("UPDATE contributions SET status = 'pending' WHERE id = ?", (c["id"],))
        raise

    status = f"✅ Approved by {escape(user_label(admin))} → {_target_label(course, material_type)} (material #{material_id})"
    if c["card_message_id"]:
        await _edit_card(c["card_chat_id"], c["card_message_id"], file_card_text(c, status), is_media=True)
    return material_id


async def commit_contribution(call: CallbackQuery, cid: int, course_id: int, material_type: str | None):
    c = await database.get_contribution(cid)
    if c is None or c["status"] != "pending":
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=None)
        return await bot.send_message(call.message.chat.id, f"Contribution #{cid} was already reviewed.")

    course = await database.get_course(course_id)

    if c["kind"] == "link":
        return await _ask_link_titles(call, c, course)

    try:
        material_id = await _approve_file(c, course, material_type, call.from_user)
    except Exception:
        return await bot.send_message(call.message.chat.id, f"❌ Failed to add contribution #{cid}. Check the logs.")
    if material_id is None:
        return

    logger.info(f"Contribution {cid} approved by {call.from_user.id} -> course {course_id}, type {material_type}, material {material_id}")
    await _notify(
        c["user_id"],
        f"✅ <b>تمت إضافة الملف للبوت!</b>\n📄 {escape(c['file_name'])}\n📚 {escape(course['name'])}\n\n<b>شكرا على مساهمتك</b> 🫡"
    )


async def commit_batch(call: CallbackQuery, batch_id: int, course_id: int, material_type: str | None):
    pending = await database.get_batch_contributions(batch_id, "pending")
    batch = await database.get_batch(batch_id)
    if not pending:
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=None)
        return await bot.send_message(call.message.chat.id, f"Batch #{batch_id} has no pending files.")

    course = await database.get_course(course_id)
    approved = 0
    for c in pending:
        try:
            if await _approve_file(c, course, material_type, call.from_user):
                approved += 1
        except Exception:
            pass
        await sleep(0.1) # stay under Telegram's edit rate limits

    total = len(await database.get_batch_contributions(batch_id))
    status = f"✅ {approved} file(s) approved by {escape(user_label(call.from_user))} → {_target_label(course, material_type)}"
    await _edit_card(call.message.chat.id, call.message.id, batch_card_text(batch, total, status), is_media=False)

    logger.info(f"Batch {batch_id} approved by {call.from_user.id}: {approved} files -> course {course_id}, type {material_type}")
    await log_to_group(f"Batch #{batch_id}: {approved} file(s) added to course {course_id} ({material_type}).")
    if approved:
        await _notify(
            batch["user_id"],
            f"✅ <b>تمت إضافة {approved} ملف من مساهمتك للبوت!</b>\n📚 {escape(course['name'])}\n\n<b>شكرا على مساهمتك</b> 🫡"
        )


async def _ask_link_titles(call: CallbackQuery, c: dict, course: dict):
    """Links need a title each: ask the admin to reply with them"""
    urls = c["urls"].split("\n")
    numbered = "\n".join(f"{i}. {escape(url)}" for i, url in enumerate(urls, 1))
    prompt = await bot.send_message(
        call.message.chat.id,
        f"✍️ <b>Reply to this message</b> with a title for each link ({len(urls)}) — one per line, in this order:\n"
        f"{numbered}\n\nThey'll be added to <b>{escape(course['name'])}</b>. Send /cancel to abort.",
        parse_mode="HTML",
        reply_to_message_id=call.message.id,
        reply_markup=ForceReply(input_field_placeholder="One title per line"),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
    state = user_states.setdefault(call.from_user.id, UserState())
    state.admin_input = {
        "action": "link_titles",
        "cid": c["id"],
        "course_id": course["id"],
        "prompt_chat": prompt.chat.id,
        "prompt_id": prompt.message_id,
    }
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⏳ Waiting for titles…", callback_data="noop"))
    markup.row(InlineKeyboardButton("✖️ Cancel", callback_data=f"rv:back:c{c['id']}"))
    await bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=markup)


async def finish_link_titles(message: Message, data: dict) -> bool:
    """Called with the admin's titles. Returns True when the input is done."""
    c = await database.get_contribution(data["cid"])
    if c is None or c["status"] != "pending":
        await bot.reply_to(message, "This contribution was already reviewed.")
        return True

    urls = c["urls"].split("\n")
    titles = [line.strip() for line in message.text.splitlines() if line.strip()]
    if len(titles) != len(urls):
        await bot.reply_to(message, f"❌ Got {len(titles)} title(s) but there are {len(urls)} link(s). Reply again, or /cancel.")
        return False

    course = await database.get_course(data["course_id"])
    if course is None:
        await bot.reply_to(message, "❌ That course no longer exists.")
        return True

    if not await database.set_contribution_status(c["id"], "approved", message.from_user.id):
        return True
    for title, url in zip(titles, urls):
        await database.add_resource(course["id"], title, url)

    status = f"✅ Approved by {escape(user_label(message.from_user))} → {_target_label(course, None)} ({len(urls)} video link(s))"
    await _edit_card(c["card_chat_id"], c["card_message_id"], link_card_text(c, status), is_media=False)
    await bot.reply_to(message, f"✅ Added {len(urls)} video link(s) to {course['name']}.")
    logger.info(f"Link contribution {c['id']} approved by {message.from_user.id} -> course {course['id']}")
    await _notify(
        c["user_id"],
        f"✅ <b>تمت إضافة اللينكات للبوت!</b>\n📚 {escape(course['name'])}\n\n<b>شكرا على مساهمتك</b> 🫡"
    )
    return True


async def cancel_review_picker(call: CallbackQuery, target_id: int, token: str):
    await bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=review_markup(token))


async def needs_type_contribution(cid: int) -> bool:
    c = await database.get_contribution(cid)
    return not (c and c["kind"] == "link")


picker.register("c", picker.PickerTarget(
    commit=commit_contribution,
    cancel=lambda call, cid: cancel_review_picker(call, cid, f"c{cid}"),
    needs_type=needs_type_contribution,
))
picker.register("b", picker.PickerTarget(
    commit=commit_batch,
    cancel=lambda call, bid: cancel_review_picker(call, bid, f"b{bid}"),
))


#===========
# Rejecting
@bot.callback_query_handler(func=lambda c: c.data.startswith("rv:"))
async def review_callback(call: CallbackQuery):
    if not isadmin(call.from_user.id):
        return await bot.answer_callback_query(call.id, "Admins only.", show_alert=True)
    await bot.answer_callback_query(call.id)

    parts = call.data.split(":")
    action, token = parts[1], parts[2]
    chat_id, message_id = call.message.chat.id, call.message.id

    if action == "r":
        return await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=reject_markup(token))

    if action == "back":
        # Also abort a pending "send titles" prompt for this card
        state = user_states.get(call.from_user.id)
        if state and state.admin_input and state.admin_input.get("action") == "link_titles" \
                and f"c{state.admin_input['cid']}" == token:
            state.admin_input = None
        return await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=review_markup(token))

    if action == "rr":
        reason_code = parts[3]
        reason_label, reason_text = REJECT_REASONS.get(reason_code, REJECT_REASONS["none"])
        status = f"❌ Rejected by {escape(user_label(call.from_user))}"
        if reason_code != "none":
            status += f" — {reason_label}"
        reason_line = f"\n<b>السبب:</b> {reason_text}" if reason_text else ""

        kind, target_id = token[0], int(token[1:])
        if kind == "c":
            c = await database.get_contribution(target_id)
            if c is None or not await database.set_contribution_status(target_id, "rejected", call.from_user.id):
                return await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
            text = link_card_text(c, status) if c["kind"] == "link" else file_card_text(c, status)
            await _edit_card(chat_id, message_id, text, is_media=c["kind"] == "file")
            what = "اللينكات" if c["kind"] == "link" else f"الملف {escape(c['file_name'])}"
            await _notify(c["user_id"], f"❌ <b>للأسف لم يتم قبول {what}.</b>{reason_line}\n\nشكرا على مساهمتك على أي حال 🙏")
            logger.info(f"Contribution {target_id} rejected by {call.from_user.id} ({reason_code})")

        elif kind == "b":
            batch = await database.get_batch(target_id)
            pending = await database.get_batch_contributions(target_id, "pending")
            rejected = 0
            for c in pending:
                if await database.set_contribution_status(c["id"], "rejected", call.from_user.id):
                    rejected += 1
                    if c["card_message_id"]:
                        await _edit_card(c["card_chat_id"], c["card_message_id"], file_card_text(c, status), is_media=True)
                        await sleep(0.1)
            total = len(await database.get_batch_contributions(target_id))
            await _edit_card(chat_id, message_id, batch_card_text(batch, total, f"{status} ({rejected} file(s))"), is_media=False)
            if rejected:
                await _notify(batch["user_id"], f"❌ <b>للأسف لم يتم قبول {rejected} ملف من مساهمتك.</b>{reason_line}\n\nشكرا على مساهمتك على أي حال 🙏")
            logger.info(f"Batch {target_id} rejected by {call.from_user.id} ({reason_code}): {rejected} files")
