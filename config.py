from dotenv import load_dotenv
from os import getenv
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
import logging
from dataclasses import dataclass

#===========
# Load Environment eariables
load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN", "")
ADMIN_ID = int(getenv("ADMIN_ID", ""))
ADMIN_GROUP = int(getenv("ADMIN_GROUP_ID", ""))
TUTORIAL_VIDEO = getenv("TUTORIAL_VIDEO_ID", "")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in the .env file.")

bot = AsyncTeleBot(BOT_TOKEN)

COLLEGE_FILE_IDS = [ # فايلات اللائحة
    x.strip() 
    for x in getenv("COLLEGE_FILES", "").split(",")
    if x.strip()
]
#===========
# Logging
logger = logging.getLogger("coolig_bot")

async def log_to_group(msg: str):
    """Sends a message to the logs group chat"""
    try:
        await bot.send_message(
            ADMIN_GROUP,
            text=msg
        )
    except Exception as e:
        logger.error(f"Failed to log to group: {e}")

#===========
# State Management
@dataclass
class UserState:
    year: int | None = None
    semester: int | None = None
    department: str | None = None
    course_id: int | None = None
    material: str | None = None
    awaiting: str | None = None # for awaiting user action
    # available states: ("doc", "link", "desc", "admin_upload")
    pending_message: Message | None = None # the pending operation message
    sent_files: int = 0 # number of files sent by the user when contributing


user_states: dict[int, UserState] = {}