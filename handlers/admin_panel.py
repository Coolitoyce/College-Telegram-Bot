"""
Admin panel (/admin), upload mode (/add_material) and admin text input (/cancel).

/admin opens an inline panel:
    Browse → Year → Semester → Course → type → material → send / rename / change type / move / delete
                                      → videos → add / rename / change URL / delete
                                      → upload here / delete course (with its materials and videos)

/add_material                  → pick a target course/type with buttons, then just send files
/add_material <CourseID> <type> → same, but set the target directly
"""
import re
from html import escape
from urllib.parse import urlparse
from telebot.types import (
    CallbackQuery, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton, Message,
    ReactionTypeEmoji, LinkPreviewOptions
)
import logging
import database
from config import bot, MATERIAL_TYPES, UserState, user_states, log_to_group
from handlers.admin import isadmin
from handlers import picker, review
from keyboards import courses as courses_kb
#===========
logger = logging.getLogger("coolig_bot")

PAGE_SIZE = 8


#===========
# Course IDs that have a button in the (hard coded) student menus
def _menu_course_ids() -> set[int]:
    ids = set()
    for value in vars(courses_kb).values():
        if isinstance(value, InlineKeyboardMarkup):
            for row in value.keyboard:
                for button in row:
                    if button.callback_data and button.callback_data.startswith("course:"):
                        ids.add(int(button.callback_data.split(":")[1]))
    return ids


MENU_COURSE_IDS = _menu_course_ids()


#===========
# Small helpers
def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text, callback_data=data)


def _type_label(material_type: str) -> str:
    return MATERIAL_TYPES.get(material_type, material_type)


async def _render(chat_id: int, message_id: int, text: str, markup: InlineKeyboardMarkup | None):
    try:
        await bot.edit_message_text(
            text, chat_id, message_id, reply_markup=markup, parse_mode="HTML",
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
    except Exception as e:
        logger.debug(f"Panel edit skipped: {e}") # usually "message is not modified"


def _username(user) -> str:
    return f"@{user.username}" if user.username else user.full_name


#===========
# Panel views: each returns (text, markup)
async def view_home():
    stats = await database.get_stats()
    text = (
        "🛠 <b>Admin Panel</b>\n\n"
        f"📚 Courses: <b>{stats['courses']}</b>\n"
        f"📄 Materials: <b>{stats['materials']}</b>\n"
        f"▶️ Videos: <b>{stats['resources']}</b>\n"
        f"📥 Pending contributions: <b>{stats['pending']}</b>"
    )
    markup = InlineKeyboardMarkup()
    markup.row(_btn("📚 Browse courses", "ap:y"))
    markup.row(_btn("📤 Upload mode", "ap:up"))
    markup.row(_btn("✖️ Close", "ap:close"))
    return text, markup


async def view_years():
    markup = InlineKeyboardMarkup()
    markup.row(_btn("Year 1", "ap:s:1"), _btn("Year 2", "ap:s:2"))
    markup.row(_btn("Year 3", "ap:s:3"), _btn("Year 4", "ap:s:4"))
    markup.row(_btn("🔙 Back", "ap:h"))
    return "📚 <b>Choose year</b>", markup


async def view_semesters(year: int):
    markup = InlineKeyboardMarkup()
    markup.row(_btn("Semester 1", f"ap:cl:{year}:1"), _btn("Semester 2", f"ap:cl:{year}:2"))
    markup.row(_btn("🔙 Back", "ap:y"), _btn("🏠 Home", "ap:h"))
    return f"📚 <b>Year {year}</b> — choose semester", markup


async def view_courses(year: int, semester: int):
    courses = await database.get_courses(year, semester) # (id, name, year, sem, dept)
    markup = InlineKeyboardMarkup()
    for course_id, name, _, _, dept in courses:
        warn = "" if course_id in MENU_COURSE_IDS else " ⚠️"
        markup.row(_btn(picker.course_label({"name": name, "department": dept}) + warn, f"ap:c:{course_id}"))
    markup.row(_btn("🔙 Back", f"ap:s:{year}"), _btn("🏠 Home", "ap:h"))
    text = f"📚 <b>Year {year} · Semester {semester}</b> — {len(courses)} course(s)"
    if any(c[0] not in MENU_COURSE_IDS for c in courses):
        text += "\n⚠️ = not in the student menus yet (add a button in keyboards/courses.py)"
    return text, markup


async def view_course(course_id: int):
    course = await database.get_course(course_id)
    if course is None:
        return "❌ This course no longer exists.", InlineKeyboardMarkup().row(_btn("🏠 Home", "ap:h"))

    counts = await database.count_materials_by_type(course_id)
    resources = await database.list_resources(course_id)
    dept = f" · {course['department']}" if course["department"] else ""
    text = (
        f"📚 <b>{escape(course['name'])}</b>\n"
        f"ID <code>{course_id}</code> · Year {course['year']} · Semester {course['semester']}{dept}\n"
    )
    if course_id not in MENU_COURSE_IDS:
        text += "⚠️ Not in the student menus — add a button with <code>course:{}</code> in keyboards/courses.py\n".format(course_id)
    unknown = {t: n for t, n in counts.items() if t not in MATERIAL_TYPES}
    if unknown:
        text += "⚠️ Materials with unknown types (students can't see them): " + \
            ", ".join(f"{escape(t)} ({n})" for t, n in unknown.items()) + "\n"

    markup = InlineKeyboardMarkup()
    buttons = [_btn(f"{label} ({counts.get(key, 0)})", f"ap:ml:{course_id}:{key}:0") for key, label in MATERIAL_TYPES.items()]
    for i in range(0, len(buttons), 2):
        markup.row(*buttons[i:i + 2])
    for t in unknown:
        markup.row(_btn(f"⚠️ {t} ({unknown[t]})", f"ap:ml:{course_id}:{t}:0"))
    markup.row(_btn(f"▶️ Videos ({len(resources)})", f"ap:rl:{course_id}"))
    markup.row(_btn("📤 Upload here", f"pk:u:t:{course_id}"), _btn("🗑 Delete course", f"ap:dc:{course_id}"))
    markup.row(_btn("🔙 Back", f"ap:cl:{course['year']}:{course['semester']}"), _btn("🏠 Home", "ap:h"))
    return text, markup


async def view_material_list(course_id: int, material_type: str, page: int):
    course = await database.get_course(course_id)
    if course is None:
        return await view_course(course_id)
    materials = await database.list_materials(course_id, material_type)
    pages = max(1, (len(materials) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(max(page, 0), pages - 1)
    chunk = materials[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]

    text = f"📚 <b>{escape(course['name'])}</b> · {_type_label(material_type)}\n{len(materials)} file(s)"
    if pages > 1:
        text += f" — page {page + 1}/{pages}"

    markup = InlineKeyboardMarkup()
    media_icons = {"photo": "🖼 ", "video": "🎬 "}
    for m in chunk:
        markup.row(_btn(f"{media_icons.get(m['media'], '')}{m['title']}"[:60], f"ap:m:{m['id']}"))
    nav = []
    if page > 0:
        nav.append(_btn("◀️", f"ap:ml:{course_id}:{material_type}:{page - 1}"))
    if page < pages - 1:
        nav.append(_btn("▶️", f"ap:ml:{course_id}:{material_type}:{page + 1}"))
    if nav:
        markup.row(*nav)
    if material_type in MATERIAL_TYPES:
        markup.row(_btn("📤 Upload to this list", f"pk:u:k:{course_id}:{material_type}"))
    markup.row(_btn("🔙 Back", f"ap:c:{course_id}"), _btn("🏠 Home", "ap:h"))
    return text, markup


async def view_material(material_id: int):
    m = await database.get_material(material_id)
    if m is None:
        return "❌ This material no longer exists.", InlineKeyboardMarkup().row(_btn("🏠 Home", "ap:h"))
    course = await database.get_course(m["course_id"])
    course_name = course["name"] if course else f"(missing course {m['course_id']})"
    text = (
        f"📄 <b>{escape(m['title'])}</b>\n\n"
        f"ID: <code>{m['id']}</code>\n"
        f"Course: {escape(course_name)} (<code>{m['course_id']}</code>)\n"
        f"Type: {_type_label(m['type'])}\n"
        f"Sent as: {m['media']}\n"
        f"Added: {m['uploaded_at']}"
    )
    markup = InlineKeyboardMarkup()
    markup.row(_btn("📤 Send file", f"ap:mf:{material_id}"), _btn("✏️ Rename", f"ap:mr:{material_id}"))
    markup.row(_btn("🔀 Change type", f"pk:m{material_id}:t:{m['course_id']}"), _btn("🚚 Move course", f"pk:m{material_id}:y"))
    markup.row(_btn("🗑 Delete", f"ap:md:{material_id}"))
    markup.row(_btn("🔙 Back", f"ap:ml:{m['course_id']}:{m['type']}:0"), _btn("🏠 Home", "ap:h"))
    return text, markup


async def view_resource_list(course_id: int):
    course = await database.get_course(course_id)
    if course is None:
        return await view_course(course_id)
    resources = await database.list_resources(course_id)
    markup = InlineKeyboardMarkup()
    for r in resources:
        markup.row(_btn(f"▶️ {r['title']}"[:60], f"ap:r:{r['id']}"))
    markup.row(_btn("➕ Add videos", f"ap:ra:{course_id}"))
    markup.row(_btn("🔙 Back", f"ap:c:{course_id}"), _btn("🏠 Home", "ap:h"))
    return f"▶️ <b>{escape(course['name'])}</b> — {len(resources)} video link(s)", markup


async def view_resource(resource_id: int):
    r = await database.get_resource(resource_id)
    if r is None:
        return "❌ This video link no longer exists.", InlineKeyboardMarkup().row(_btn("🏠 Home", "ap:h"))
    text = (
        f"▶️ <b>{escape(r['title'])}</b>\n\n"
        f"ID: <code>{r['id']}</code>\n"
        f"URL: {escape(r['url'])}\n"
        f"Added: {r['uploaded_at']}"
    )
    markup = InlineKeyboardMarkup()
    markup.row(_btn("✏️ Rename", f"ap:rr:{resource_id}"), _btn("🔗 Change URL", f"ap:ru:{resource_id}"))
    markup.row(_btn("🗑 Delete", f"ap:rd:{resource_id}"))
    markup.row(_btn("🔙 Back", f"ap:rl:{r['course_id']}"), _btn("🏠 Home", "ap:h"))
    return text, markup


def _confirm_markup(yes: str, no: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(_btn("✅ Yes, delete", yes), _btn("✖️ Cancel", no))
    return markup


#===========
# Upload mode
def _upload_status(state: UserState, course: dict, private: bool):
    course_id, material_type = state.upload_target
    text = (
        "📤 <b>Upload mode ON</b>\n\n"
        f"Target: <b>{escape(course['name'])}</b> (<code>{course_id}</code>) · {_type_label(material_type)}\n"
        f"Added this session: <b>{state.uploaded_files}</b>\n\n"
        "Send or forward files here (documents, photos, videos) — each one is added automatically.\n"
        "<i>A caption like</i> <code>12|exam</code> <i>overrides the target for that file.</i>"
    )
    if not private:
        text += "\n\n⚠️ Uploads only work in your private chat with the bot."
    markup = InlineKeyboardMarkup()
    markup.row(_btn("🔄 Change target", "pk:u:y"), InlineKeyboardButton("End ❌", callback_data="end_admin_upload", style="primary"))
    return text, markup


async def _start_upload(state: UserState, course_id: int, material_type: str):
    if state.awaiting != "admin_upload":
        state.uploaded_files = 0
    state.awaiting = "admin_upload"
    state.upload_target = (course_id, material_type)
    state.last_target = (course_id, material_type)


async def _end_upload(user) -> str:
    state = user_states.setdefault(user.id, UserState())
    added = state.uploaded_files
    state.awaiting = None
    state.upload_target = None
    state.uploaded_files = 0
    logger.info(f"User {user.id}({_username(user)}) ended upload mode, {added} file(s) added.")
    await log_to_group(f"User {user.id}({_username(user)}) ended upload mode: {added} file(s) added.")
    return f"*Upload mode ended* ❌\nAdded {added} file(s)."


async def commit_upload_target(call: CallbackQuery, _, course_id: int, material_type: str):
    state = user_states.setdefault(call.from_user.id, UserState())
    await _start_upload(state, course_id, material_type)
    course = await database.get_course(course_id)
    logger.info(f"User {call.from_user.id}({_username(call.from_user)}) set upload target: course {course_id}, {material_type}")
    text, markup = _upload_status(state, course, call.message.chat.type == "private")
    await _render(call.message.chat.id, call.message.id, text, markup)


async def cancel_upload_picker(call: CallbackQuery, _):
    state = user_states.setdefault(call.from_user.id, UserState())
    if state.awaiting == "admin_upload" and state.upload_target:
        course = await database.get_course(state.upload_target[0])
        if course:
            text, markup = _upload_status(state, course, call.message.chat.type == "private")
            return await _render(call.message.chat.id, call.message.id, text, markup)
    await _render(call.message.chat.id, call.message.id, "Upload mode not started. ✖️", None)


picker.register("u", picker.PickerTarget(commit=commit_upload_target, cancel=cancel_upload_picker))


@bot.message_handler(commands=['add_material'])
async def add_material_command(message: Message):
    """Starts/ends upload mode"""
    if not isadmin(message.from_user.id):
        return
    state = user_states.setdefault(message.from_user.id, UserState())
    args = message.text.split(maxsplit=1)

    if len(args) == 1:
        if state.awaiting == "admin_upload":
            return await bot.reply_to(message, await _end_upload(message.from_user), parse_mode="Markdown")
        return await bot.reply_to(
            message,
            "📤 <b>Where should uploaded files go?</b>",
            reply_markup=await picker.years_markup("u", message.from_user.id),
            parse_mode="HTML"
        )

    parts = re.split(r"[\s|]+", args[1].strip())
    usage = "*Usage:*\n`/add_material` — choose with buttons\n`/add_material <CourseID> <type>`\n\nTypes: " + \
        ", ".join(f"`{t}`" for t in MATERIAL_TYPES)
    if len(parts) != 2 or not parts[0].isdigit():
        return await bot.reply_to(message, usage, parse_mode="Markdown")
    course_id, material_type = int(parts[0]), parts[1].lower()
    if material_type not in MATERIAL_TYPES:
        return await bot.reply_to(message, f"❌ Unknown type `{material_type}`.\n\n" + usage, parse_mode="Markdown")
    course = await database.get_course(course_id)
    if course is None:
        return await bot.reply_to(message, f"❌ No course with ID {course_id}.")

    await _start_upload(state, course_id, material_type)
    text, markup = _upload_status(state, course, message.chat.type == "private")
    await bot.reply_to(message, text, reply_markup=markup, parse_mode="HTML")
    logger.info(f"User {message.from_user.id}({_username(message.from_user)}) started upload mode: course {course_id}, {material_type}")


@bot.callback_query_handler(func=lambda c: c.data == "end_admin_upload")
async def end_admin_upload(call: CallbackQuery):
    if not isadmin(call.from_user.id):
        return await bot.answer_callback_query(call.id, "Admins only.", show_alert=True)
    await bot.answer_callback_query(call.id)
    text = await _end_upload(call.from_user)
    await bot.edit_message_text(text, call.message.chat.id, call.message.id, parse_mode="Markdown")


CAPTION_TARGET = re.compile(r"^\s*(\d+)\s*\|\s*(\w+)\s*$")


async def handle_admin_upload(message: Message):
    """Adds a file sent in upload mode as a material (called from main.handle_files)"""
    state = user_states.setdefault(message.from_user.id, UserState())
    caption = (message.caption or "").strip()

    target = state.upload_target
    override = CAPTION_TARGET.match(caption)
    if override:
        target = (int(override.group(1)), override.group(2).lower())
        caption = ""
    if target is None:
        return await bot.reply_to(
            message,
            "❌ No upload target. Use /add_material to choose one, or caption the file with `<CourseID>|<type>`.",
            parse_mode="Markdown"
        )

    course_id, material_type = target
    if material_type not in MATERIAL_TYPES:
        return await bot.reply_to(message, f"❌ Unknown type `{material_type}`. Types: " + ", ".join(MATERIAL_TYPES), parse_mode="Markdown")
    if await database.get_course(course_id) is None:
        return await bot.reply_to(message, f"❌ No course with ID {course_id}.")

    if message.content_type == "photo":
        media, file_id, title = "photo", message.photo[-1].file_id, caption or "Photo"
    elif message.content_type == "video":
        media, file_id, title = "video", message.video.file_id, message.video.file_name or caption or "Video"
    else:
        media, file_id, title = "document", message.document.file_id, message.document.file_name or caption or "File"

    try:
        material_id = await database.add_material(course_id, title, material_type, file_id, media)
    except Exception:
        logger.exception(f"Admin upload failed: user={message.from_user.id} course={course_id} type={material_type} file_id={file_id}")
        await log_to_group(f"Admin upload failed: user={message.from_user.id} course={course_id} type={material_type}")
        return await bot.reply_to(message, "❌ Failed to add material.")

    state.uploaded_files += 1
    logger.info(f"Admin upload: user={message.from_user.id} material={material_id} course={course_id} type={material_type} media={media}")
    try:
        await bot.set_message_reaction(message.chat.id, message.id, [ReactionTypeEmoji("👍")])
    except Exception:
        await bot.reply_to(message, f"✅ Added (material #{material_id}).")


#===========
# Material move / change type (picker target "m")
async def commit_material_move(call: CallbackQuery, material_id: int, course_id: int, material_type: str):
    m = await database.get_material(material_id)
    if m is not None:
        await database.update_material(material_id, course_id=course_id, type=material_type)
        await log_to_group(f"Material {material_id} moved to course {course_id} ({material_type}) by {_username(call.from_user)}")
    text, markup = await view_material(material_id)
    await _render(call.message.chat.id, call.message.id, text, markup)


async def cancel_material_move(call: CallbackQuery, material_id: int):
    text, markup = await view_material(material_id)
    await _render(call.message.chat.id, call.message.id, text, markup)


picker.register("m", picker.PickerTarget(commit=commit_material_move, cancel=cancel_material_move))


#===========
# Panel
@bot.message_handler(commands=['admin'])
async def admin_panel(message: Message):
    if not isadmin(message.from_user.id):
        return
    text, markup = await view_home()
    await bot.reply_to(message, text, reply_markup=markup, parse_mode="HTML")


async def _ask_input(call: CallbackQuery, prompt: str, data: dict):
    """Asks the admin for text and remembers what it's for"""
    sent = await bot.send_message(
        call.message.chat.id,
        prompt + "\n\nSend /cancel to abort.",
        parse_mode="HTML",
        reply_markup=ForceReply(),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
    state = user_states.setdefault(call.from_user.id, UserState())
    state.admin_input = {
        **data,
        "prompt_chat": sent.chat.id,
        "prompt_id": sent.message_id,
        "panel_chat": call.message.chat.id,
        "panel_id": call.message.id,
    }


@bot.callback_query_handler(func=lambda c: c.data.startswith("ap:"))
async def panel_callback(call: CallbackQuery):
    if not isadmin(call.from_user.id):
        return await bot.answer_callback_query(call.id, "Admins only.", show_alert=True)

    parts = call.data.split(":")
    view, args = parts[1], parts[2:]
    chat_id, message_id = call.message.chat.id, call.message.id
    result = None

    if view == "close":
        await bot.answer_callback_query(call.id)
        return await bot.delete_message(chat_id, message_id)

    elif view == "mf": # send the file itself
        m = await database.get_material(int(args[0]))
        if m is None:
            return await bot.answer_callback_query(call.id, "Material not found.", show_alert=True)
        await bot.answer_callback_query(call.id)
        send = {"photo": bot.send_photo, "video": bot.send_video}.get(m["media"], bot.send_document)
        try:
            return await send(chat_id, m["telegram_file_id"], caption=f"#{m['id']} · {m['title']}"[:1024])
        except Exception as e:
            logger.error(f"Failed to send material {m['id']}: {e}")
            return await bot.send_message(chat_id, f"❌ Telegram couldn't send this file: {escape(str(e))}", parse_mode="HTML")

    elif view in ("mr", "rr", "ru", "ra"): # text inputs
        target_id = int(args[0])
        item = None
        if view == "mr":
            item = await database.get_material(target_id)
        elif view in ("rr", "ru"):
            item = await database.get_resource(target_id)
        elif view == "ra":
            item = await database.get_course(target_id)
        if item is None:
            return await bot.answer_callback_query(call.id, "Not found (deleted?).", show_alert=True)
        await bot.answer_callback_query(call.id)

        if view == "mr":
            return await _ask_input(call, f"✏️ Send the new name for <b>{escape(item['title'])}</b>:", {"action": "rename_material", "id": target_id})
        if view == "rr":
            return await _ask_input(call, f"✏️ Send the new title for <b>{escape(item['title'])}</b>:", {"action": "rename_resource", "id": target_id})
        if view == "ru":
            return await _ask_input(call, f"🔗 Send the new URL for <b>{escape(item['title'])}</b>:", {"action": "resource_url", "id": target_id})
        return await _ask_input(
            call,
            "➕ Send the videos to add, one per line:\n<code>Title | URL</code>",
            {"action": "add_resources", "id": target_id}
        )

    await bot.answer_callback_query(call.id)

    if view == "h":
        result = await view_home()
    elif view == "y":
        result = await view_years()
    elif view == "s":
        result = await view_semesters(int(args[0]))
    elif view == "cl":
        result = await view_courses(int(args[0]), int(args[1]))
    elif view == "c":
        result = await view_course(int(args[0]))
    elif view == "ml":
        result = await view_material_list(int(args[0]), args[1], int(args[2]))
    elif view == "m":
        result = await view_material(int(args[0]))
    elif view == "rl":
        result = await view_resource_list(int(args[0]))
    elif view == "r":
        result = await view_resource(int(args[0]))

    elif view == "up":
        state = user_states.setdefault(call.from_user.id, UserState())
        course = await database.get_course(state.upload_target[0]) if state.upload_target else None
        if state.awaiting == "admin_upload" and course:
            result = _upload_status(state, course, call.message.chat.type == "private")
        else:
            result = ("📤 <b>Where should uploaded files go?</b>", await picker.years_markup("u", call.from_user.id))

    # Deletions (ask first, then do it)
    elif view == "md":
        m = await database.get_material(int(args[0]))
        if m:
            result = (f"🗑 Delete <b>{escape(m['title'])}</b>?", _confirm_markup(f"ap:mdy:{m['id']}", f"ap:m:{m['id']}"))
    elif view == "mdy":
        m = await database.get_material(int(args[0]))
        if m and await database.remove_material(m["id"]):
            await log_to_group(f"Material {m['id']} ({m['title']}) removed by {_username(call.from_user)}")
            result = await view_material_list(m["course_id"], m["type"], 0)
    elif view == "rd":
        r = await database.get_resource(int(args[0]))
        if r:
            result = (f"🗑 Delete <b>{escape(r['title'])}</b>?", _confirm_markup(f"ap:rdy:{r['id']}", f"ap:r:{r['id']}"))
    elif view == "rdy":
        r = await database.get_resource(int(args[0]))
        if r and await database.remove_resource(r["id"]):
            await log_to_group(f"Resource {r['id']} ({r['title']}) removed by {_username(call.from_user)}")
            result = await view_resource_list(r["course_id"])
    elif view == "dc":
        course = await database.get_course(int(args[0]))
        if course:
            counts = await database.count_materials_by_type(course["id"])
            videos = len(await database.list_resources(course["id"]))
            result = (
                f"🗑 Delete <b>{escape(course['name'])}</b> with <b>{sum(counts.values())}</b> file(s) "
                f"and <b>{videos}</b> video link(s)?\n\n⚠️ This can't be undone. "
                "Remember to remove its button from keyboards/courses.py too.",
                _confirm_markup(f"ap:dcy:{course['id']}", f"ap:c:{course['id']}")
            )
    elif view == "dcy":
        course = await database.get_course(int(args[0]))
        if course:
            _, materials, resources = await database.remove_course_cascade(course["id"])
            await log_to_group(
                f"Course {course['id']} ({course['name']}) removed by {_username(call.from_user)} "
                f"with {materials} materials and {resources} resources"
            )
            result = await view_courses(course["year"], course["semester"])

    if result is None: # item disappeared meanwhile
        result = await view_home()
    await _render(chat_id, message_id, *result)


#===========
# Admin text input (rename, new URL, add videos, link titles)
def _is_admin_input(message: Message) -> bool:
    if not isadmin(message.from_user.id):
        return False
    state = user_states.get(message.from_user.id)
    if not state or not state.admin_input or not message.text or message.text.startswith("/"):
        return False
    data = state.admin_input
    if message.chat.id != data.get("prompt_chat"):
        return False
    if message.chat.type == "private":
        return True
    # In groups only accept replies to the prompt (so normal chatting isn't swallowed)
    return bool(message.reply_to_message and message.reply_to_message.message_id == data.get("prompt_id"))


def _valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


@bot.message_handler(func=_is_admin_input, content_types=["text"])
async def admin_input_handler(message: Message):
    state = user_states[message.from_user.id]
    data = state.admin_input
    action = data["action"]
    text = message.text.strip()
    done = True
    refresh = None # view to re-render on the panel message

    if action == "link_titles":
        done = await review.finish_link_titles(message, data)

    elif action == "rename_material":
        if await database.update_material(data["id"], title=text):
            await bot.reply_to(message, "✅ Renamed.")
            refresh = await view_material(data["id"])

    elif action == "rename_resource":
        if await database.update_resource(data["id"], title=text):
            await bot.reply_to(message, "✅ Renamed.")
            refresh = await view_resource(data["id"])

    elif action == "resource_url":
        if not _valid_url(text):
            await bot.reply_to(message, "❌ That isn't a valid http(s) link. Send it again, or /cancel.")
            done = False
        elif await database.update_resource(data["id"], url=text):
            await bot.reply_to(message, "✅ URL updated.")
            refresh = await view_resource(data["id"])

    elif action == "add_resources":
        entries, bad = [], []
        for line in text.splitlines():
            if not line.strip():
                continue
            title, sep, url = line.rpartition("|")
            if not sep or not title.strip() or not _valid_url(url.strip()):
                bad.append(line)
            else:
                entries.append((title.strip(), url.strip()))
        if bad or not entries:
            await bot.reply_to(
                message,
                "❌ Every line must look like <code>Title | https://...</code>\nProblem lines:\n" +
                escape("\n".join(bad) or "(none)") + "\n\nSend them again, or /cancel.",
                parse_mode="HTML"
            )
            done = False
        else:
            for title, url in entries:
                await database.add_resource(data["id"], title, url)
            await log_to_group(f"{len(entries)} resource(s) added to course {data['id']} by {_username(message.from_user)}")
            await bot.reply_to(message, f"✅ Added {len(entries)} video link(s).")
            refresh = await view_resource_list(data["id"])

    if done:
        state.admin_input = None
    if refresh and data.get("panel_id"):
        await _render(data["panel_chat"], data["panel_id"], *refresh)


@bot.message_handler(commands=["cancel"])
async def cancel_input(message: Message):
    if not isadmin(message.from_user.id):
        return
    state = user_states.get(message.from_user.id)
    if not state or not state.admin_input:
        return await bot.reply_to(message, "Nothing to cancel.")
    data = state.admin_input
    state.admin_input = None
    if data["action"] == "link_titles":
        c = await database.get_contribution(data["cid"])
        if c and c["status"] == "pending":
            try:
                await bot.edit_message_reply_markup(c["card_chat_id"], c["card_message_id"], reply_markup=review.review_markup(f"c{c['id']}"))
            except Exception:
                pass
    await bot.reply_to(message, "Cancelled. ✖️")
