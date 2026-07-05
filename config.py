from dotenv import load_dotenv
from os import getenv
from telebot.async_telebot import AsyncTeleBot

# Load Environment eariables
#===========
load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN", "")
ADMIN_ID = int(getenv("ADMIN_ID", ""))
LOGS_GROUP = getenv("LOGS_GROUP_ID", "")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in the .env file.")

bot = AsyncTeleBot(BOT_TOKEN)

COLLEGE_FILE_IDS = [ # فايلات اللائحة
    x.strip() 
    for x in getenv("COLLEGE_FILES", "").split(",")
    if x.strip()
]

#===========