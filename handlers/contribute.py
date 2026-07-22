from config import bot, log_to_group, ADMIN_GROUP, UserState, user_states
from telebot.types import Message, CallbackQuery, ReactionTypeEmoji
import logging
from keyboards.primary import contribute_markup, cancel_markup, end_contribute_markup
from urllib.parse import urlparse
#===========
logger = logging.getLogger("coolig_bot")

#===========
# Handle contribute
@bot.message_handler(func=lambda m: m.text == "Contribute 🤝")
async def hande_contribute(message: Message):
    reply_msg = (
        "*عندك ماتريال حابب تضيفها للبوت؟*\n"
        "*اختر نوع الماتريال اللي حابب تضيفها وهيتم مراجعتها وفي حال التأكد هتتضاف للبوت.* ⬇️"
    )

    await bot.reply_to(
        message,
        reply_msg,
        reply_markup=contribute_markup,
        parse_mode="Markdown"
    )


#===========
# Handle contribute callback
@bot.callback_query_handler(func=lambda c: c.data.startswith("send:"))
async def handle_contribute_call(call: CallbackQuery):
    await bot.answer_callback_query(call.id)
    option = call.data.split(":", maxsplit=1)[1]
    state = user_states.setdefault(call.from_user.id, UserState())

    if option == "doc":
        state.awaiting = "doc"
        state.pending_message = call.message
        await bot.edit_message_text(
            "*في انتظارك حتى ترسل الفايلات...* ⌚\n*عند الانتهاء اضغط على انهاء ✅*",
            call.message.chat.id,
            call.message.id,
            reply_markup=end_contribute_markup,
            parse_mode="Markdown"
        )

    elif option == "link":
        state.awaiting = "link"
        state.pending_message = call.message
        await bot.edit_message_text(
            "*في انتظارك حتى ترسل اللينك...* ⌚",
            call.message.chat.id,
            call.message.id,
            reply_markup=cancel_markup,
            parse_mode="Markdown"
        )
#===========
# Handle contribution completion
@bot.callback_query_handler(func=lambda c: c.data in ["finish_send", "cancel_send"])
async def handle_end_contribute(call: CallbackQuery):
    await bot.answer_callback_query(call.id)

    state = user_states.setdefault(call.from_user.id, UserState())
    state.awaiting = None
    if call.data == "finish_send":
        await bot.edit_message_text(
            "*تم انهاء العملية.* ✅",
            call.message.chat.id,
            call.message.id,
            parse_mode="Markdown"
        )

        if state.sent_files > 0:
            reply_msg = (
                "*تم استلام الفايلات بنجاح!* ✅\n\n"
                "هيتم مراجعة الفايلات وفي حالة التأكد هتتضاف للبوت.\n"
                "*شكرا على مساهمتك* 🫡"
            )
            await bot.reply_to(
                call.message,
                reply_msg,
                parse_mode="Markdown"
            )
        
    elif call.data == "cancel_send":
        await bot.edit_message_text(
            "*تم الغاء العملية.* ❌",
            call.message.chat.id,
            call.message.id,
            parse_mode="Markdown"
        )
    state.sent_files = 0

#===========
# Handle sending files
async def handle_file_contribute(message: Message):
    state = user_states.setdefault(message.from_user.id, UserState())
    state.sent_files += 1
    await bot.set_message_reaction(
        message.chat.id,
        message.id,
        [ReactionTypeEmoji("❤️")],
    )
    await bot.forward_message(
        ADMIN_GROUP,
        message.chat.id,
        message.id,
    )
    if message.content_type == "document":
        file_name = message.document.file_name
        file_id = message.document.file_id

    elif message.content_type == "photo":
        file_name = "photo"
        file_id = message.photo[-1].file_id

    elif message.content_type == "video":
        file_name = message.video.file_name
        file_id = message.video.file_id

    logger.info(
        f"User {message.from_user.id}({message.from_user.username}) sent {message.content_type} with name={file_name}, ID={file_id}"
    )
    await log_to_group(
        f"User {message.from_user.id}({message.from_user.username}) sent {message.content_type} with name={file_name}"
    )

#===========
def is_valid_url(url: str) -> bool:
    "Checks if the provided link is a valid URL"
    parsed = urlparse(url)
    return all([parsed.scheme in ("http", "https"), bool(parsed.netloc), bool(parsed.path) or bool(parsed.query)])

#===========
# Handle sending links
async def handle_link_contribute(message: Message):
    state = user_states.setdefault(message.from_user.id, UserState())
    if state.awaiting == "link":
        if is_valid_url(message.text.strip()):
            state.awaiting = None
            await bot.edit_message_text(
                "*تم انهاء العملية.* ✅",
                message.chat.id,
                state.pending_message.id,
                parse_mode="Markdown"
            )

            await bot.forward_message(
                ADMIN_GROUP,
                message.chat.id,
                message.id
            )

            logger.info(f"User {message.from_user.id}({message.from_user.username}) sent a link: {message.text}")
            reply_msg = (
                "*تم استلام اللينك!* ✅\n\n"
                "هيتم مراجعة اللينك وفي حالة التأكد هيتضاف للبوت.\n"
                "*شكرا على مساهمتك* 🫡"
            )
            await bot.reply_to(
                message,
                reply_msg,
                parse_mode="Markdown"
            )

        else:
            state.awaiting = None
            await bot.edit_message_text(
                "*تم انهاء العملية.* ❌",
                message.chat.id,
                state.pending_message.id,
                parse_mode="Markdown"
            )
            reply_msg = (
                "*اللينك ده غير صحيح* ❌\n\n"
                "*لازم اللينك يبدأ بـ* `http` *أو* `https` *ويكون لينك كامل، ومتبعتش أكتر من لينك.*\n"
                "*ارجع الى قائمة Contribute 🤝 للمحاولة من جديد.*"
            )

            await bot.reply_to(
                message,
                reply_msg,
                parse_mode="Markdown"
            )