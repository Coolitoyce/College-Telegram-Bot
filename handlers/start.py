from config import bot, UserState, user_states, log_to_group 
from telebot.types import CallbackQuery, InputMediaDocument
from keyboards import courses, materials as materials_kb, primary
import logging
import database
from asyncio import sleep
#=====================
logger = logging.getLogger("coolig_bot")

#=====================
# Year Handler
@bot.callback_query_handler(func=lambda c: c.data.startswith("year"))
async def year_handler(call: CallbackQuery):
    await bot.answer_callback_query(call.id)
    
    year = int(call.data.split(":")[1])
    state = user_states.setdefault(call.from_user.id, UserState())
    state.year = year

    years = ["المستوى الأول", "المستوى الثاني", "المستوى الثالث", "المستوى الرابع"]
    year_text = years[year-1]
    if year >= 3:
        await bot.edit_message_text(
            f"لقد اخترت *{year_text}*\n---\nاختر القسم",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=primary.dept_markup,
            parse_mode="Markdown"
        )

    else:
        await bot.edit_message_text(
            f"لقد اخترت *{year_text}*\n---\nاختر الترم",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=primary.semester_markup,
            parse_mode="Markdown"
        )


#=====================
# Semester Handler
@bot.callback_query_handler(func=lambda c: c.data.startswith("sem"))
async def semester_handler(call: CallbackQuery):
    await bot.answer_callback_query(call.id)
    
    semester = int(call.data.split(":")[1])
    state = user_states.setdefault(call.from_user.id, UserState())
    state.semester = semester

    year = state.year
    username = call.from_user.username if call.from_user.username else call.from_user.full_name
    if year is None:
        logger.error(f"Error: User {call.from_user.id}({username}) tried to access an old menu, year not set.")
        return await bot.reply_to(
            call.message,
            f"*خطأ!* ❌\nيبدو أنك تحاول الوصول إلى قائمة قديمة\nاعمل واحدة جديدة من */start* أو اضغط على *القائمة الرئيسية* 🔝",
            parse_mode="Markdown"
        )

    if year == 1:
        if semester == 1:
            markup = courses.year1_sem1_markup
            semester_text = "الأول"

        elif semester == 2:
            markup = courses.year1_sem2_markup
            semester_text = "الثاني"
     
    elif year == 2:
        if semester == 1:
            markup = courses.year2_sem1_markup
            semester_text = "الأول"

        elif semester == 2:
            markup = courses.year2_sem2_markup
            semester_text = "الثاني"

    else:
        markup = primary.back_markup
        return await bot.edit_message_text(
            "لسه موصلتش السنة دي 😛",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )  
    
    await bot.edit_message_text(
        f"لقد اخترت *الترم {semester_text}*\n---\nاختر المادة",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )


#=====================
# Department Handler
@bot.callback_query_handler(func=lambda c: c.data.startswith("dept"))
async def department_handler(call: CallbackQuery):
    await bot.answer_callback_query(call.id)
    
    dept = call.data.split(":")[1]
    state = user_states.setdefault(call.from_user.id, UserState())
    state.department = dept

    await bot.edit_message_text(
        f"لقد اخترت قسم *{dept.upper()}*\n---\nاختر الترم",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=primary.semester_markup,
        parse_mode="Markdown"
    )


#=====================
# Course Handler
@bot.callback_query_handler(func= lambda c: c.data.startswith("course"))
async def course_handler(call: CallbackQuery):
    await bot.answer_callback_query(call.id)
    
    course_id = int(call.data.split(":")[1])
    state = user_states.setdefault(call.from_user.id, UserState())
    state.course_id = course_id

    semester = state.semester
    username = call.from_user.username if call.from_user.username else call.from_user.full_name
    if semester is None:
        logger.error(f"Error: User {call.from_user.id}({username}) tried to access an old menu, semester not set.")
        return await bot.reply_to(
            call.message,
            f"*خطأ!* ❌\nيبدو أنك تحاول الوصول إلى قائمة قديمة\nاعمل واحدة جديدة من */start* أو اضغط على *القائمة الرئيسية* 🔝",
            parse_mode="Markdown"
        )

    course_name = await database.get_course_name(course_id)

    await bot.edit_message_text(
        f"لقد اخترت *{course_name}*\nاختر نوع الماتريال",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=materials_kb.materials_markup(semester),
        parse_mode="Markdown"
    )


#=====================
# Material Handler
@bot.callback_query_handler(func = lambda c: c.data.startswith("material"))
async def material_handler(call: CallbackQuery):
    await bot.answer_callback_query(call.id)
    
    material_type = (call.data.split(":")[1])
    state = user_states.setdefault(call.from_user.id, UserState())

    course_id = state.course_id
    username = call.from_user.username if call.from_user.username else call.from_user.full_name
    if course_id is None:
        logger.error(f"Error: User {call.from_user.id}({username}) tried to access an old menu, course id not set.")
        return await bot.reply_to(
            call.message,
            f"*خطأ!* ❌\nيبدو أنك تحاول الوصول إلى قائمة قديمة\nاعمل واحدة جديدة من */start* أو اضغط على *القائمة الرئيسية* 🔝",
            parse_mode="Markdown"
        )

    materials = await database.get_materials(course_id, material_type) # materials (id, course_id, title, type, file_id, uploaded_at)
    media_group = []
    for material in materials:
        media_group.append(InputMediaDocument(material[4]))

    username = call.from_user.username if call.from_user.username else call.from_user.full_name
    if len(media_group) == 0:
        logger.info(f"Tried sending material of type {material_type} for course {course_id}({await database.get_course_name(course_id)}) to user {call.from_user.id}({username}) but couldn't find any.")
        return await bot.edit_message_text(
            "*مفيش ماتريال من النوع ده للمادة دي.* ❌",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=materials_kb.back_markup(course_id),
            parse_mode="Markdown"
        )

    else:
        await bot.edit_message_text(
            "*تم إرسال الماتريال المطلوبة*\nللرجوع شوف الرسالة تحت الملفات ⬇️",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        
    for i in range(0, len(media_group), 10):
        await bot.send_media_group(
            call.message.chat.id,
            media_group[i:i+10]
        )
        await sleep(0.2)

    username = call.from_user.username if call.from_user.username else call.from_user.full_name
    logger.info(f"Sent materials of type {material_type} for course {course_id}({await database.get_course_name(course_id)}) to user {call.from_user.id}({username})")
    await bot.send_message(
        call.message.chat.id,
        "*What next?*",
        reply_markup=materials_kb.back_markup(course_id),
        parse_mode="Markdown"
    )


#=====================
# Extra Resources (Videos) Handler
@bot.callback_query_handler(func=lambda c: c.data.startswith("resource"))
async def resource_handler(call: CallbackQuery):
    await bot.answer_callback_query(call.id)

    state = user_states.setdefault(call.from_user.id, UserState)

    course_id = state.course_id
    username = call.from_user.username if call.from_user.username else call.from_user.full_name
    if course_id is None:
        logger.error(f"Error: User {call.from_user.id}({username}) tried to access an old menu, course id not set.")
        return await bot.reply_to(
            call.message,
            f"*خطأ!* ❌\nيبدو أنك تحاول الوصول إلى قائمة قديمة\nاعمل واحدة جديدة من */start* أو اضغط على *القائمة الرئيسية* 🔝",
            parse_mode="Markdown"
        )

    resources = await database.get_resources(course_id) # resources (id, course_id, title, url, uploaded_at)

    clean_resources = []
    for resource in resources:
        clean_resources.append((resource[2], resource[3])) # Append title and URL
    
    if len(clean_resources) == 0:
        await bot.edit_message_text(
            "*مفيش فيديوهات للمادة دي.* ❌",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=materials_kb.back_markup(course_id),
            parse_mode="Markdown"
        )

    else:
        markup = materials_kb.resources_markup(course_id, clean_resources)

        await bot.edit_message_text(
            "اختر من القائمة",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )


#=====================
# Home Callback Handler
@bot.callback_query_handler(func=lambda c: c.data.startswith("home"))
async def callback(call: CallbackQuery):
    await bot.answer_callback_query(call.id)

    await bot.edit_message_text(
        "اختر الفرقة",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=primary.year_markup
    )