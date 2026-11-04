"""
Inline course/type picker shared by the admin features.

Every picker is attached to a "target" token that tells it what to do with the result:
    u      -> set the admin's upload target            (handlers/admin_panel.py)
    m<ID>  -> move material <ID> / change its type     (handlers/admin_panel.py)
    c<ID>  -> approve contribution <ID>                 (handlers/review.py)
    b<ID>  -> approve every pending file in batch <ID>  (handlers/review.py)

Callback data: pk:<target>:<step>[:args]
    y              -> choose year
    s:<y>          -> choose semester
    c:<y>:<s>      -> choose course
    t:<course>     -> choose material type
    k:<course>:<t> -> commit (type is "-" when the target doesn't need a type)
    x              -> cancel
"""
from dataclasses import dataclass
from typing import Awaitable, Callable
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import database
from config import bot, MATERIAL_TYPES, UserState, user_states
from handlers.admin import isadmin
#===========
logger = logging.getLogger("coolig_bot")


#===========
@dataclass
class PickerTarget:
    # commit(call, target_id, course_id, material_type or None)
    commit: Callable[[CallbackQuery, int | None, int, str | None], Awaitable]
    # cancel(call, target_id)
    cancel: Callable[[CallbackQuery, int | None], Awaitable]
    # needs_type(target_id) -> whether a material type must be chosen
    needs_type: Callable[[int | None], Awaitable[bool]] | None = None


TARGETS: dict[str, PickerTarget] = {}


def register(kind: str, target: PickerTarget):
    """Registers what a picker of the given kind does on commit/cancel"""
    TARGETS[kind] = target


def split_target(token: str) -> tuple[str, int | None]:
    kind, rest = token[0], token[1:]
    return kind, int(rest) if rest else None


async def _needs_type(token: str) -> bool:
    kind, target_id = split_target(token)
    target = TARGETS[kind]
    return await target.needs_type(target_id) if target.needs_type else True


def _noop(text: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text, callback_data="noop")


def course_label(course: dict) -> str:
    label = course["name"]
    if course.get("department"):
        label += f" · {course['department']}"
    return label[:60]


#===========
# Keyboards
async def years_markup(token: str, admin_id: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(_noop("📍 Choose year"))

    # Quick button: same course/type as the last pick
    state = user_states.get(admin_id)
    if state and state.last_target:
        course_id, material_type = state.last_target
        course = await database.get_course(course_id)
        if course:
            needs_type = await _needs_type(token)
            label = course["name"] + (f" · {MATERIAL_TYPES.get(material_type, material_type)}" if needs_type else "")
            markup.row(InlineKeyboardButton(
                f"⚡ {label}"[:60],
                callback_data=f"pk:{token}:k:{course_id}:{material_type if needs_type else '-'}"
            ))

    markup.row(
        InlineKeyboardButton("Year 1", callback_data=f"pk:{token}:s:1"),
        InlineKeyboardButton("Year 2", callback_data=f"pk:{token}:s:2"),
    )
    markup.row(
        InlineKeyboardButton("Year 3", callback_data=f"pk:{token}:s:3"),
        InlineKeyboardButton("Year 4", callback_data=f"pk:{token}:s:4"),
    )
    markup.row(InlineKeyboardButton("✖️ Cancel", callback_data=f"pk:{token}:x"))
    return markup


def semesters_markup(token: str, year: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(_noop(f"📍 Year {year} · choose semester"))
    markup.row(
        InlineKeyboardButton("Semester 1", callback_data=f"pk:{token}:c:{year}:1"),
        InlineKeyboardButton("Semester 2", callback_data=f"pk:{token}:c:{year}:2"),
    )
    markup.row(
        InlineKeyboardButton("🔙 Back", callback_data=f"pk:{token}:y"),
        InlineKeyboardButton("✖️ Cancel", callback_data=f"pk:{token}:x"),
    )
    return markup


async def courses_markup(token: str, year: int, semester: int) -> InlineKeyboardMarkup:
    needs_type = await _needs_type(token)
    courses = await database.get_courses(year, semester) # (id, name, year, sem, dept)
    markup = InlineKeyboardMarkup()
    markup.row(_noop(f"📍 Year {year} · Semester {semester} · choose course"))
    if not courses:
        markup.row(_noop("(no courses here)"))
    for course_id, name, _, _, dept in courses:
        label = course_label({"name": name, "department": dept})
        data = f"pk:{token}:t:{course_id}" if needs_type else f"pk:{token}:k:{course_id}:-"
        markup.row(InlineKeyboardButton(label, callback_data=data))
    markup.row(
        InlineKeyboardButton("🔙 Back", callback_data=f"pk:{token}:s:{year}"),
        InlineKeyboardButton("✖️ Cancel", callback_data=f"pk:{token}:x"),
    )
    return markup


async def types_markup(token: str, course_id: int) -> InlineKeyboardMarkup | None:
    course = await database.get_course(course_id)
    if course is None:
        return None
    markup = InlineKeyboardMarkup()
    markup.row(_noop(f"📍 {course['name']} · choose type"[:60]))
    buttons = [
        InlineKeyboardButton(label, callback_data=f"pk:{token}:k:{course_id}:{key}")
        for key, label in MATERIAL_TYPES.items()
    ]
    for i in range(0, len(buttons), 2):
        markup.row(*buttons[i:i + 2])
    markup.row(
        InlineKeyboardButton("🔙 Back", callback_data=f"pk:{token}:c:{course['year']}:{course['semester']}"),
        InlineKeyboardButton("✖️ Cancel", callback_data=f"pk:{token}:x"),
    )
    return markup


#===========
@bot.callback_query_handler(func=lambda c: c.data == "noop")
async def noop_handler(call: CallbackQuery):
    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("pk:"))
async def picker_handler(call: CallbackQuery):
    if not isadmin(call.from_user.id):
        return await bot.answer_callback_query(call.id, "Admins only.", show_alert=True)

    parts = call.data.split(":")
    token, step, args = parts[1], parts[2], parts[3:]
    kind, target_id = split_target(token)
    target = TARGETS.get(kind)
    if target is None:
        return await bot.answer_callback_query(call.id, "Unknown picker.", show_alert=True)

    chat_id, message_id = call.message.chat.id, call.message.id

    if step == "x":
        await bot.answer_callback_query(call.id)
        return await target.cancel(call, target_id)

    if step == "k":
        course_id = int(args[0])
        material_type = None if args[1] == "-" else args[1]
        if material_type is not None and material_type not in MATERIAL_TYPES:
            return await bot.answer_callback_query(call.id, "Unknown material type.", show_alert=True)
        if await database.get_course(course_id) is None:
            return await bot.answer_callback_query(call.id, "That course no longer exists.", show_alert=True)

        state = user_states.setdefault(call.from_user.id, UserState())
        if material_type is not None:
            state.last_target = (course_id, material_type)

        await bot.answer_callback_query(call.id)
        return await target.commit(call, target_id, course_id, material_type)

    if step == "y":
        markup = await years_markup(token, call.from_user.id)
    elif step == "s":
        markup = semesters_markup(token, int(args[0]))
    elif step == "c":
        markup = await courses_markup(token, int(args[0]), int(args[1]))
    elif step == "t":
        markup = await types_markup(token, int(args[0]))
        if markup is None:
            return await bot.answer_callback_query(call.id, "That course no longer exists.", show_alert=True)
    else:
        return await bot.answer_callback_query(call.id)

    await bot.answer_callback_query(call.id)

    try:
        await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=markup)
    except Exception as e:
        # "message is not modified" when pressing the same button twice
        logger.debug(f"Picker edit skipped: {e}")
