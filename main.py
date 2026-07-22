import telebot
import asyncio
import logging
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, LinkPreviewOptions
#=====
import database
from keyboards import primary
from config import bot, COLLEGE_FILE_IDS, TUTORIAL_VIDEO, user_states, UserState
from handlers.admin import *
from handlers.start import *
from handlers.contribute import *
#=====================
# Logging
logger = logging.getLogger("coolig_bot")
logger.setLevel(logging.INFO)
logger.propagate = False

handler = logging.FileHandler("bot.log", encoding="utf-8")
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s",
    "%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

telebot.logger.setLevel(logging.INFO)

#=====================
# Start Command
@bot.message_handler(commands=['start'])
async def start(message: Message):
    state = user_states.setdefault(message.from_user.id, UserState())
    if state.awaiting == "doc":
        return await bot.reply_to(
            state.pending_message,
            "*البوت في انتظارك حتى تنهي عملية إرسال الفايلات.* ❌",
            parse_mode="Markdown"
        )
    elif state.awaiting == "link":
        return await bot.reply_to(
            state.pending_message,
            "*البوت في انتظارك حتى تنهي عملية إرسال اللينك.* ❌",
            parse_mode="Markdown"
        )    
    
    intro_message = (
        "<b>السلام عليكم</b> 👋\n\n"
        "في البوت ده إن شاء الله هتلاقي ماتريال لكل مواد الكلية من أولى لرابعة 🌠\n"
        "لو في أي مشكلة حصلت معاك ياريت تتواصل معايا 👐\n"
        "ولو عندك ماتريال حابب تضيفها للبوت اضغط على <b>Contribute 🤝</b> من القائمة تحت\n\n"
        "<b>نصيحة:</b> اقفل التنزيل التلقائي في التيليجرام عشان متنزلش كل الفايلات مرة واحدة على جهازك 🫠\n\n"
        "<b>اختر من القائمة</b> 🔥\n\n"
        "<blockquote><b>ملحوظة:</b> لو فاتح من <b>تيليجرام ويب</b>، القائمة هتكون في الزرار اللي جنب زرار الريكورد/الكاميرا.</blockquote>"
    )

    if message.chat.type != "private":
        return await bot.send_message(
            message.chat.id,
            "*البوت يعمل فقط في الشات البرايڤت.* ❌",
            parse_mode="Markdown"
        )
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        KeyboardButton(
            "📚 Materials",
            style="primary"
        )
    )
    markup.row("لائحة الكلية الجديدة 📜")
    markup.row("لينك البوت 🐧", "🤖 About")
    markup.row(
        "فيديو توضيحي 🎥",
        KeyboardButton(
            "Contribute 🤝",
            style="success"            
        )
    )

    await bot.send_message(
        message.chat.id,
        intro_message,
        reply_markup=markup,
        parse_mode="HTML"
    )

    logger.info(f"User {message.from_user.id}({message.from_user.username}) executed /start.")
    await log_to_group(f"User {message.from_user.id}({message.from_user.username}) executed /start.")

#=====================
# Handle Regular Messages
@bot.message_handler(func=lambda m: not m.text.startswith('/start'))
async def handle_keyboard(message: Message):
    message.text = message.text.strip()
    state = user_states.setdefault(message.from_user.id, UserState())

    if state.awaiting == "link":
        return await handle_link_contribute(message)

    elif state.awaiting == "doc":
        return await bot.reply_to(
            state.pending_message,
            "*البوت في انتظارك حتى تنهي عملية إرسال الفايلات.* ❌",
            parse_mode="Markdown"
        )

    if message.text == "📚 Materials":
        await bot.send_message(
            message.chat.id,
            "اختر الفرقة",
            reply_markup=primary.year_markup
        )

    elif message.text == "لينك البوت 🐧":
        await bot.reply_to(
            message,
            f"*Username:* @fci\\_coolig28\\_bot\n*Link:* https://t.me/fci\\_coolig28\\_bot",
            parse_mode="Markdown"
        )

    elif message.text == "🤖 About":
        await bot.reply_to(
            message,
            f"<b>Made with ♥️ by @coolitoyce</b>.\n<b>Using the <a href='https://github.com/eternnoir/pyTelegramBotAPI'>pyTelegramBotAPI</a> Python Library</b>.\n\n<b><blockquote><a href='https://github.com/Coolitoyce/College-Telegram-Bot'>View GitHub Repository</a></blockquote></b>",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            parse_mode="HTML"
        )

    elif message.text == "لائحة الكلية الجديدة 📜":
        files = [
            InputMediaDocument(x)
            for x in COLLEGE_FILE_IDS
        ]
        await bot.send_media_group(
            message.chat.id,
            files
        )

    elif message.text == "فيديو توضيحي 🎥":
        await bot.send_video(
            message.chat.id,
            TUTORIAL_VIDEO
        )

    else:
        error_msg = "*أمر غير معرف!* ❌\nلا ترسل رسائل مباشرة في شات البوت\nلإعادة تحميل القائمة اضغط */start*"
        await bot.reply_to(
            message,
            error_msg,
            parse_mode="Markdown"
        )

#=====================
# Basic check for Unknown commands from non admin users
@bot.message_handler(func=lambda m: m.text.startswith('/'))
async def handle_messages(message: Message):
    state = user_states.setdefault(message.from_user.id, UserState())
    if state.awaiting == "doc":
        return await bot.reply_to(
            state.pending_message,
            "*البوت في انتظارك حتى تنهي عملية إرسال الفايلات.* ❌",
            parse_mode="Markdown"
        )
    elif state.awaiting == "link":
        return await bot.reply_to(
            state.pending_message,
            "*البوت في انتظارك حتى تنهي عملية إرسال اللينك.* ❌",
            parse_mode="Markdown"
        )   

    if not isadmin(message.from_user.id):
        error_msg = "*أمر غير معرف!* ❌\nلا ترسل رسائل مباشرة في شات البوت\nلإعادة تحميل القائمة اضغط */start*"
        await bot.reply_to(
            message,
            error_msg,
            parse_mode="Markdown"
        )  

#=====================
# Handle receiving files
@bot.message_handler(content_types=["document", "photo", "video"])
async def handle_files(message: Message):
    state = user_states.setdefault(message.from_user.id, UserState())
    if state.awaiting == "doc":
        return await handle_file_contribute(message)
    
    elif state.awaiting == "admin_upload":
        return await handle_admin_upload(message)

    else:
        await bot.reply_to(
            message,
            "*لو عايز تبعت الماتريال بتاعتك لازم تختار Contribute 🤝 من القائمة أولاً.* ❌",
            parse_mode="Markdown"
        )

#=====================
async def main():
    await database.ready_tables()

    logger.info(f"Starting the bot with username: [@fci_coolig28_bot]")
    await bot.polling()  

if __name__ == "__main__":
    asyncio.run(main())
    
#=====================