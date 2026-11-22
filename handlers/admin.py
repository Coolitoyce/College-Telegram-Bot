from config import bot, log_to_group, ADMIN_ID, UserState, user_states
from telebot.types import Message, CallbackQuery,InlineKeyboardMarkup, InlineKeyboardButton
import logging
import database
#===========
logger = logging.getLogger("coolig_bot")

#===========
def isadmin(id: int) -> bool:
    """Checks if the user is an admin"""
    if id == ADMIN_ID:
        return True      
    return False


#=============================================================================
# Validation helpers
# Why: These helpers stop bad numbers and incomplete pipe-separated commands
# before they reach SQLite. This is safer and gives the admin a clear usage error.

def parse_integer(value: str, field_name: str):
    """Converts a string to a positive integer and returns a clear error."""
    try:
        parsed = int(value.strip())
    except (AttributeError, ValueError):
        return None, f"❌ {field_name} must be a whole number."

    if parsed <= 0:
        return None, f"❌ {field_name} must be greater than zero."

    return parsed, None


def parse_pipe_parts(text: str, expected_count: int):
    """Splits a | command and rejects empty values before database operations."""
    parts = [part.strip() for part in text.split('|')]

    if len(parts) != expected_count:
        return None, f"❌ Incorrect Arguments. Expected {expected_count} values separated by |."

    for part in parts:
        if not part:
            return None, "❌ Empty values are not allowed."

    return parts, None


async def course_exists(course_id: int) -> bool:
    """Checks that a course really exists; this prevents orphaned materials/resources."""
    course_name = await database.get_course_name(course_id)
    return course_name is not None


#=============================================================================
# Admin result-card formatting
# Why: IDs and context make result cards useful for follow-up remove commands.

def material_result_cards(materials: list) -> str:
    """Formats materials as: ID • title • course • type."""
    if not materials:
        return "<i>No materials found.</i>"

    lines = []
    for material in materials:
        material_id = material[0]
        course_id = material[1]
        title = material[2]
        material_type = material[3]
        course_name = database_course_names.get(course_id, f"Course {course_id}")
        lines.append(f"<b>{material_id}</b> • {title} • {course_name} • {material_type}")

    return "\n".join(lines)


def resource_result_cards(resources: list) -> str:
    """Formats resources as: ID • title • course • resource."""
    if not resources:
        return "<i>No resources found.</i>"

    lines = []
    for resource in resources:
        resource_id = resource[0]
        course_id = resource[1]
        title = resource[2]
        course_name = database_course_names.get(course_id, f"Course {course_id}")
        lines.append(f"<b>{resource_id}</b> • {title} • {course_name} • resource")

    return "\n".join(lines)


async def refresh_database_course_names():
    """Builds a small course-ID cache only for displaying readable admin cards."""
    global database_course_names
    database_course_names = {}
    courses = await database.get_courses()
    for course in courses:
        database_course_names[course[0]] = course[1]


database_course_names = {}

#=============================================================================
# /admin dashboard
# Why: A button menu is faster than remembering every command and provides a
# clear starting point for bulk upload and database management.

@bot.message_handler(commands=['admin'])
async def admin_dashboard(message: Message):
    """Shows the admin dashboard in private chats."""
    if not isadmin(message.from_user.id):
        return

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📤 Bulk upload", callback_data="admin:bulk"),
        InlineKeyboardButton("➕ Add material", callback_data="admin:add_material")
    )
    markup.row(
        InlineKeyboardButton("📚 Courses", callback_data="admin:courses"),
        InlineKeyboardButton("📄 Materials", callback_data="admin:materials")
    )
    markup.row(
        InlineKeyboardButton("🔗 Resources", callback_data="admin:resources")
    )
    markup.row(
        InlineKeyboardButton("❓ Admin help", callback_data="admin:help")
    )

    await bot.reply_to(
        message,
        "<b>Admin Dashboard</b> 🛠️\n\nChoose an action:",
        reply_markup=markup,
        parse_mode="HTML"
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("admin:"))
async def handle_admin_dashboard(call: CallbackQuery):
    await bot.answer_callback_query(call.id)

    if not isadmin(call.from_user.id):
        return

    action = call.data.split(":", maxsplit=1)[1]

    if action == "bulk":
        await bot.edit_message_text(
            "<b>Bulk upload</b>\n\n"
            "Send this command:\n"
            "<code>/bulk_upload &lt;CourseID&gt;|&lt;Type&gt;</code>\n\n"
            "Example: <code>/bulk_upload 15|lecture</code>",
            call.message.chat.id,
            call.message.id,
            parse_mode="HTML"
        )

    elif action == "add_material":
        await bot.edit_message_text(
            "<b>Add material</b>\n\n"
            "Send <code>/add_material</code>, then upload files with a caption.\n"
            "Each caption must be <code>&lt;CourseID&gt;|&lt;Type&gt;</code>.",
            call.message.chat.id,
            call.message.id,
            parse_mode="HTML"
        )

    elif action == "courses":
        await bot.edit_message_text(
            "Use <code>/get_courses</code> to view courses.",
            call.message.chat.id,
            call.message.id,
            parse_mode="HTML"
        )

    elif action == "materials":
        await bot.edit_message_text(
            "Use <code>/get_materials &lt;CourseID&gt;</code> to view a course's cards.",
            call.message.chat.id,
            call.message.id,
            parse_mode="HTML"
        )

    elif action == "resources":
        await bot.edit_message_text(
            "Use <code>/get_resources &lt;CourseID&gt;</code> to view resource cards.",
            call.message.chat.id,
            call.message.id,
            parse_mode="HTML"
        )

    elif action == "help":
        await bot.edit_message_text(
            "Send <code>/admin_help</code> for the full command list.",
            call.message.chat.id,
            call.message.id,
            parse_mode="HTML"
        )


#===========
# Command to list all admin commands and their correct usages
@bot.message_handler(commands=['admin_help'])
async def admin_help(message: Message):
    """Sends a list of all admin commands and their correct usages"""
    if isadmin(message.from_user.id):
        help_text = (
            "<b>Admin Commands:</b>\n\n"
            "<blockquote>"
            "<code>/admin</code> - Opens the admin dashboard.\n"
            "<code>/admin_help</code> - Shows this help message.\n"
            "<code>/userinfo</code> - Gets the current user's info.\n"
            "<code>/chatinfo</code> - Gets the current chat's info.\n"
            "<code>/add_material</code> - Enables the admin upload material state.\n"
            "<code>/bulk_upload (CourseID)|(Type)</code> - Uploads many files to the same course/type.\n"
            "<code>/get_file (FileID)</code> - Sends a file from a given ID.\n"
            "<code>/add_resource (CourseID)|(Title)|(URL)</code> - Adds a new resource to the database.\n"
            "<code>/add_course (Course Name)|(Year)|(Semester)|(Department)</code> - Adds a new course to the database.\n"
            "<code>/remove_course (CourseID)</code> - Removes a course from the database.\n"
            "<code>/remove_resource (ResourceID)</code> - Removes a resource from the database.\n"
            "<code>/remove_material (MaterialID)</code> - Removes a material from the database.\n"
            "<code>/get_courses [Year] [Semester] [Department]</code> - Gets courses in the database.\n"
            "<code>/get_materials (CourseID) [Type]</code> - Gets materials in the database.\n"
            "<code>/get_resources (CourseID)</code> - Gets resources in the database.\n"
            "<code>/id</code> - Gets the current chat ID."
            "</blockquote>"
        )
        await bot.reply_to(
            message,
            help_text,
            parse_mode="HTML"
        )


#===========
@bot.message_handler(commands=['get_file'])
async def get_file(message: Message):
    """Sends a file from a given ID"""
    if isadmin(message.from_user.id):
        args = message.text.split(maxsplit=1)
        if len(args) != 2:
            return await bot.reply_to(message, "*Usage:*\n`/get_file <FileID>`", parse_mode="Markdown")

        file_id = args[1]
        try:
            await bot.send_document(message.chat.id, file_id)

        except Exception:
            logger.exception("Failed to send document file_id=%s user_id=%s chat_id=%s", file_id, message.from_user.id, message.chat.id)
            return await bot.reply_to(message, "A file with that ID doesn't exist.")


#=============================================================================
# Handle admin upload of materials
async def handle_admin_upload(message: Message):
    """Adds one file in normal upload mode or one file in bulk upload mode."""
    state = user_states.setdefault(message.from_user.id, UserState())

    if message.content_type == "video":
        file_id = message.video.file_id
        file_name = message.video.file_name or "Video"
    elif message.content_type == "photo":
        file_id = message.photo[-1].file_id
        file_name = "Photo"
    else:
        file_id = message.document.file_id
        file_name = message.document.file_name or "Document"

    # Bulk mode uses one CourseID and Type for all files, so it does not need a caption.
    if state.awaiting == "bulk_upload":
        course_id = state.bulk_course_id
        material_type = state.bulk_material_type

    else:
        # Normal admin mode deliberately requires a caption; this avoids guessing
        # what course or material type a standalone file belongs to.
        if message.caption is None:
            return await bot.reply_to(
                message,
                "❌ *Missing Caption*\n*Usage:*\n`<CourseID>|<Type>`",
                parse_mode="Markdown"
            )

        parts, error = parse_pipe_parts(message.caption, 2)
        if error:
            return await bot.reply_to(message, error)

        course_id, error = parse_integer(parts[0], "Course ID")
        if error:
            return await bot.reply_to(message, error)

        material_type = parts[1].lower()

    allowed_types = {"lecture", "section", "summary", "practical", "exam", "book", "video"}
    if material_type not in allowed_types:
        return await bot.reply_to(
            message,
            "❌ Material type must be one of: lecture, section, summary, practical, exam, book, video"
        )

    if not await course_exists(course_id):
        return await bot.reply_to(message, f"❌ Course ID {course_id} does not exist.")

    try:
        await database.add_material(course_id, file_name, material_type, file_id)
        logger.info("Admin upload successful: userID=%s course_id=%s content_type=%s", message.from_user.id, course_id, message.content_type)
        await log_to_group(f"Added a new material with: course id={course_id}, file name={file_name}, material type={material_type}")
        await bot.reply_to(message, f"Got it! ✅\nAdded to course {course_id} as {material_type}.")

    except Exception:
        username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
        logger.error(
            "Admin upload failed: userID=%s username=%s course_id=%s content_type=%s file_id=%s",
            message.from_user.id,
            username,
            course_id,
            message.content_type,
            file_id,
            exc_info=True
        )
        await log_to_group(f"Admin upload failed: user={message.from_user.id} username={username} course_id={course_id} content_type={message.content_type} file_id={file_id}")
        await bot.reply_to(message, "❌ Failed to add material.")


#===========
# Handle enabling admin upload material state
@bot.message_handler(commands=['add_material'])
async def enable_admin_upload(message: Message):
    """Enables the admin upload material state"""
    state = user_states.setdefault(message.from_user.id, UserState())
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    if isadmin(message.from_user.id):
        if state.awaiting == "admin_upload":
            state.awaiting = None
            await bot.reply_to(
                message,
                "*Admin Upload Material State Disabled* ❌",
                parse_mode="Markdown"
            )
            logger.info(f"User {message.from_user.id}({username}) disabled admin upload state.")
            await log_to_group(f"User {message.from_user.id}({username}) disabled admin upload state.")

        else:
            state.awaiting = "admin_upload"
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton(
                    "End ❌",
                    callback_data="end_admin_upload",
                    style="primary"
                )
            )

            await bot.reply_to(
                message,
                "*Admin Upload Material State Enabled*\n\nNow you can send a file with the caption `<CourseID>|<Type>` to add a new material to the database.",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            logger.info(f"User {message.from_user.id}({username}) enabled admin upload state.")
            await log_to_group(f"User {message.from_user.id}({username}) enabled admin upload state.")


#===========
# Handle disabling admin upload material state
@bot.callback_query_handler(func=lambda c: c.data == "end_admin_upload")
async def end_admin_upload(call: CallbackQuery):
    await bot.answer_callback_query(call.id)
    state = user_states.setdefault(call.from_user.id, UserState())

    if isadmin(call.from_user.id):
        state.awaiting = None
        await bot.edit_message_text(
            "*Admin Upload Material State Disabled* ❌",
            call.message.chat.id,
            call.message.id,
            parse_mode="Markdown"
        )
        username = f"@{call.from_user.username}" if call.from_user.username else call.from_user.full_name
        logger.info(f"User {call.from_user.id}({username}) disabled admin upload state.")
        await log_to_group(f"User {call.from_user.id}({username}) disabled admin upload state.")


#=============================================================================
# Bulk upload mode
# Why: Repeating CourseID|Type on every file is slow. This mode stores those
# values once, then applies them to every document/photo/video uploaded next.

@bot.message_handler(commands=['bulk_upload'])
async def enable_bulk_upload(message: Message):
    """Starts bulk upload mode for an exact course and material type."""
    if not isadmin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        return await bot.reply_to(
            message,
            "*Usage:*\n`/bulk_upload <CourseID>|<Type>`\nExample: `/bulk_upload 15|lecture`",
            parse_mode="Markdown"
        )

    parts, error = parse_pipe_parts(args[1], 2)
    if error:
        return await bot.reply_to(message, error)

    course_id, error = parse_integer(parts[0], "Course ID")
    if error:
        return await bot.reply_to(message, error)

    if not await course_exists(course_id):
        return await bot.reply_to(message, f"❌ Course ID {course_id} does not exist.")

    material_type = parts[1].lower()
    allowed_types = {"lecture", "section", "summary", "practical", "exam", "book"}
    if material_type not in allowed_types:
        return await bot.reply_to(
            message,
            "❌ Material type must be one of: lecture, section, summary, practical, exam, book, video"
        )

    state = user_states.setdefault(message.from_user.id, UserState())
    state.awaiting = "bulk_upload"
    state.bulk_course_id = course_id
    state.bulk_material_type = material_type

    course_name = await database.get_course_name(course_id)
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("End ❌", callback_data="end_bulk_upload", style="primary")
    )

    await bot.reply_to(
        message,
        f"<b>Bulk upload enabled</b> ✅\n\n"
        f"Course: <b>{course_name}</b> (ID {course_id})\n"
        f"Type: <b>{material_type}</b>\n\n"
        "Now send files without captions.",
        reply_markup=markup,
        parse_mode="HTML"
    )


@bot.callback_query_handler(func=lambda c: c.data == "end_bulk_upload")
async def end_bulk_upload(call: CallbackQuery):
    await bot.answer_callback_query(call.id)

    if not isadmin(call.from_user.id):
        return

    state = user_states.setdefault(call.from_user.id, UserState())
    state.awaiting = None
    state.bulk_course_id = None
    state.bulk_material_type = None

    await bot.edit_message_text(
        "Bulk upload ended. ❌",
        call.message.chat.id,
        call.message.id
    )


#===========
@bot.message_handler(commands=['add_resource'])
async def add_resource(message: Message):
    """Adds a new resource to the database"""
    if isadmin(message.from_user.id):
        args = message.text.split(maxsplit=1)
        if len(args) != 2:
            return await bot.reply_to(
                message,
                "*Usage:*\n`/add_resource <CourseID>|<Title>|<URL>`",
                parse_mode="Markdown"
            )
        args, error = parse_pipe_parts(args[1], 3)
        if error:
            return await bot.reply_to(
                message,
                f"{error}\n*Usage:*\n`/add_resource <CourseID>|<Title>|<URL>`",
                parse_mode="Markdown"
            )

        course_id, error = parse_integer(args[0], "Course ID")
        if error:
            return await bot.reply_to(message, error)

        if not await course_exists(course_id):
            return await bot.reply_to(message, f"❌ Course ID {course_id} does not exist.")

        title = args[1]
        url = args[2]
        
        try:
            await database.add_resource(course_id, title, url)
            await log_to_group(f"Added a new resource with: course_id={course_id}, title={title}, url={url}")
            await bot.reply_to(message, "Resource added successfully. ✅")

        except Exception as e:
            logger.error(f"Failed to add resource: {e}")
            await log_to_group(f"Failed to add resource: {e}")
            return await bot.reply_to(message, "❌ Failed to add the resource.")


#===========
@bot.message_handler(commands=['add_course'])
async def add_course(message: Message):
    """Adds a new course to the database"""
    if isadmin(message.from_user.id):
        args = message.text.split(maxsplit=1)
        if len(args) != 2:
            return await bot.reply_to(
                message,
                "*Usage:*\n`/add_course <Course Name>|<Year>|<Semester>|<Department>`",
                parse_mode="Markdown"
            )
        
        if len([part for part in args[1].split('|')]) not in (3, 4):
            return await bot.reply_to(
                message,
                "❌ *Incorrect Arguments*\n*Usage:*\n`/add_course <Course Name>|<Year>|<Semester>|<Department>`",
                parse_mode="Markdown"
            )

        parts = [part.strip() for part in args[1].split('|')]
        if any(not part for part in parts):
            return await bot.reply_to(message, "❌ Empty values are not allowed.")

        course_name = parts[0]
        year, error = parse_integer(parts[1], "Year")
        if error:
            return await bot.reply_to(message, error)

        sem, error = parse_integer(parts[2], "Semester")
        if error:
            return await bot.reply_to(message, error)

        if year not in (1, 2, 3, 4):
            return await bot.reply_to(message, "❌ Year must be between 1 and 4.")

        if sem not in (1, 2):
            return await bot.reply_to(message, "❌ Semester must be 1 or 2.")

        dept = parts[3].upper() if len(parts) == 4 else None
        
        try:
            await database.add_course(course_name, year, sem, dept)
            await log_to_group(f"Added a new course with: name={course_name}, year={year}, semester={sem}, department={dept}")
            await bot.reply_to(message, "Course added successfully. ✅")

        except Exception as e:
            logger.error(f"Failed to add course: {e}")
            await log_to_group(f"Failed to add course: {e}")
            return await bot.reply_to(message, "❌ Failed to add the course.")


#===========
@bot.message_handler(commands=['remove_course'])
async def remove_course(message: Message):
    """Removes a course from the database"""
    if isadmin(message.from_user.id):
        args = message.text.split(maxsplit=1)
        if len(args) != 2:
            return await bot.reply_to(
                message,
                "*Usage:*\n`/remove_course <CourseID>`",
                parse_mode="Markdown"
            )
        
        course_id, error = parse_integer(args[1], "Course ID")
        if error:
            return await bot.reply_to(message, error)

        if not await course_exists(course_id):
            return await bot.reply_to(message, f"❌ Course ID {course_id} does not exist.")

        try:
            await database.remove_course(course_id)
            await log_to_group(f"Removed course with ID: {course_id}")
            await bot.reply_to(
                message,
                "Course removed successfully. ✅"
            )

        except Exception as e:
            logger.error(f"Failed to remove course: {e}")
            await log_to_group(f"Failed to remove course: {e}")
            return await bot.reply_to(message, "❌ Failed to remove the course.")

#===========
@bot.message_handler(commands=['remove_resource'])
async def remove_resource(message: Message):
    """Removes a resource from the database"""
    if isadmin(message.from_user.id):
        args = message.text.split(maxsplit=1)
        if len(args) != 2:
            return await bot.reply_to(
                message,
                "*Usage:*\n`/remove_resource <ResourceID>`",
                parse_mode="Markdown"
            )
        
        resource_id, error = parse_integer(args[1], "Resource ID")
        if error:
            return await bot.reply_to(message, error)

        try:
            removed = await database.remove_resource(resource_id)
            if not removed:
                return await bot.reply_to(message, f"❌ Resource ID {resource_id} does not exist.")
            await log_to_group(f"Removed resource with ID: {resource_id}")
            await bot.reply_to(
                message,
                "Resource removed successfully. ✅"
            )

        except Exception as e:
            logger.error(f"Failed to remove resource: {e}")
            await log_to_group(f"Failed to remove resource: {e}")
            return await bot.reply_to(message, "❌ Failed to remove the course.")


#===========
@bot.message_handler(commands=['remove_material'])
async def remove_material(message: Message):
    """Removes a material from the database"""
    if isadmin(message.from_user.id):
        args = message.text.split(maxsplit=1)
        if len(args) != 2:
            return await bot.reply_to(
                message,
                "*Usage:*\n`/remove_material <MaterialID>`",
                parse_mode="Markdown"
            )
        
        material_id, error = parse_integer(args[1], "Material ID")
        if error:
            return await bot.reply_to(message, error)

        try:
            removed = await database.remove_material(material_id)
            if not removed:
                return await bot.reply_to(message, f"❌ Material ID {material_id} does not exist.")
            await log_to_group(f"Removed material with ID: {material_id}")
            await bot.reply_to(
                message,
                "Material removed successfully. ✅"
            )

        except Exception as e:
            logger.error(f"Failed to remove material: {e}")
            await log_to_group(f"Failed to remove material: {e}")
            return await bot.reply_to(message, "❌ Failed to remove the material.")


#===========
@bot.message_handler(commands=['get_courses'])
async def get_courses(message: Message):
    """Gets courses in the database"""
    if isadmin(message.from_user.id):
        args = message.text.split(maxsplit=3)
        dept = None
        year = None
        semeseter = None
        if len(args) == 2:
            year, error = parse_integer(args[1], "Year")
            if error:
                return await bot.reply_to(message, error)

        elif len(args) == 3:
            year, error = parse_integer(args[1], "Year")
            if error:
                return await bot.reply_to(message, error)

            semeseter, error = parse_integer(args[2], "Semester")
            if error:
                return await bot.reply_to(message, error)
        
        elif len(args) == 4:
            year, error = parse_integer(args[1], "Year")
            if error:
                return await bot.reply_to(message, error)

            semeseter, error = parse_integer(args[2], "Semester")
            if error:
                return await bot.reply_to(message, error)

            dept = args[3].upper()

        if year is not None and year not in (1, 2, 3, 4):
            return await bot.reply_to(message, "❌ Year must be between 1 and 4.")

        if semeseter is not None and semeseter not in (1, 2):
            return await bot.reply_to(message, "❌ Semester must be 1 or 2.")
        
        reply_msg = ""
        if dept:
            courses = await database.get_courses(year, semeseter, dept) # courses = (id, name, year, sem, dept)
            reply_msg += f"\n<b>Year {year}, Semester {semeseter}, Department {dept} Courses</b>\n<blockquote>"
            for course in courses: 
                reply_msg += f"<b>{course[1]}</b>\nID: {course[0]}\n\n"
            
            reply_msg += "</blockquote>"

        elif semeseter:
            courses = await database.get_courses(year, semeseter) 
            reply_msg += f"\n<b>Year {year}, Semester {semeseter} Courses</b>\n<blockquote>"
            for course in courses: 
                reply_msg += f"<b>{course[1]}</b>\nID: {course[0]}\nDepartment: {course[4]}\n\n"
            
            reply_msg += "</blockquote>"

        elif year:
            courses = await database.get_courses(year=year)
            reply_msg += f"\n<b>Year {year} Courses</b>\n<blockquote expandable>"
            for course in courses: 
                reply_msg += f"<b>{course[1]}</b>\nID: {course[0]}\nSemester: {course[3]}\nDepartment: {course[4]}\n\n"

            reply_msg += "</blockquote>"

        else:
            courses = await database.get_courses() 
            for i in range(1, 5):
                reply_msg += f"=====\n<b>Year {i} Courses</b>\n<blockquote expandable>"
                found_course = False
                for course in courses: 
                    if course[2] == i:
                        found_course = True
                        reply_msg += f"<b>{course[1]}</b>\nID: {course[0]}\nSemester: {course[3]}\nDepartment: {course[4]}\n\n"

                if not found_course:
                    reply_msg += "</blockquote>\n"
                else:
                    reply_msg += "</blockquote>"
        
        try:
            await bot.reply_to(message, reply_msg, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Failed to send courses list: {e}")
            await log_to_group(f"Failed to send courses list: {e}")
            await bot.reply_to(message, "❌ Failed to send the courses list.")


#===========
@bot.message_handler(commands=['get_materials'])
async def get_materials(message: Message):
    """Gets materials in the database"""
    if isadmin(message.from_user.id):
        args = message.text.split()
        course_id = None
        material_type = None

        if len(args) == 3:
            course_id, error = parse_integer(args[1], "Course ID")
            if error:
                return await bot.reply_to(message, error)

            material_type = args[2].lower()

        elif len(args) == 2:
            course_id, error = parse_integer(args[1], "Course ID")
            if error:
                return await bot.reply_to(message, error)

        if course_id is not None and not await course_exists(course_id):
            return await bot.reply_to(message, f"❌ Course ID {course_id} does not exist.")

        if material_type:
            allowed_types = {"lecture", "section", "summary", "practical", "exam", "book", "video"}
            if material_type not in allowed_types:
                return await bot.reply_to(
                    message,
                    "❌ Material type must be one of: lecture, section, summary, practical, exam, book, video"
                )

        reply_msg = ""
        await refresh_database_course_names()
        if material_type:
            materials = await database.get_materials(course_id, material_type) # materials = (id, course_id, title, type, telegram_file_id, uploaded_at)
            reply_msg += f"\n<b>Course {course_id} Materials of Type {material_type}</b>\n<blockquote expandable>"
            reply_msg += material_result_cards(materials)
            reply_msg += "</blockquote>"

        elif course_id:
            materials = await database.get_materials(course_id)
            reply_msg += f"\n<b>Course {course_id} Materials</b>\n<blockquote expandable>"
            reply_msg += material_result_cards(materials)
            reply_msg += "</blockquote>"

        else:
            materials = await database.get_materials()
            max_course_id = -1
            for x in materials:
                if x[1] > max_course_id:
                    max_course_id = x[1]

            for i in range(1, max_course_id + 1):
                reply_msg += f"=====\n<b>Course {i} Materials</b>\n<blockquote expandable>"
                found_material = False
                for material in materials: 
                    if material[1] == i:
                        found_material = True
                        reply_msg += f"<b>{material[2]}</b>\nID: {material[0]}\nType: {material[3]}\nTelegram File ID: {material[4]}\nUploaded at: {material[5]}\n\n"

                if not found_material:
                    reply_msg += "</blockquote>\n"
                else:
                    reply_msg += "</blockquote>"
        
        try:
            await bot.reply_to(message, reply_msg, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Failed to send materials list: {e}")
            await log_to_group(f"Failed to send materials list: {e}")
            await bot.reply_to(message, "❌ Failed to send the materials list.")

            


#===========
@bot.message_handler(commands=['get_resources'])
async def get_resources(message: Message):
    """Gets resources in the database"""
    if isadmin(message.from_user.id):
        args = message.text.split()
        course_id = None
        if len(args) == 2:
            course_id, error = parse_integer(args[1], "Course ID")
            if error:
                return await bot.reply_to(message, error)

        reply_msg = ""
        await refresh_database_course_names()
        if course_id:
            resources = await database.get_resources(course_id) # resources = (id, course_id, title, url, uploaded_at)
            reply_msg += f"\n<b>Course {course_id} Resources</b>\n<blockquote expandable>"
            reply_msg += resource_result_cards(resources)
            reply_msg += "</blockquote>"

        else:
            resources = await database.get_resources()
            max_course_id = -1
            for x in resources:
                if x[1] > max_course_id:
                    max_course_id = x[1]

            for i in range(1, max_course_id + 1):
                reply_msg += f"=====\n<b>Course {i} Resources</b>\n<blockquote expandable>"
                found_resource = False
                for resource in resources: 
                    if resource[1] == i:
                        found_resource = True
                        reply_msg += f"<b>{resource[2]}</b>\nID: {resource[0]}\nURL: {resource[3]}\nUploaded at: {resource[4]}\n\n"

                if not found_resource:
                    reply_msg += "</blockquote>\n"
                else:
                    reply_msg += "</blockquote>"
        
        try:
            await bot.reply_to(message, reply_msg, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Failed to send resources list: {e}")
            await log_to_group(f"Failed to send resources list: {e}")
            await bot.reply_to(message, "❌ Failed to send the resources list.")


#===========
@bot.message_handler(commands=['userinfo'])
async def userinfo(message: Message):
    """Gets user info"""
    if isadmin(message.from_user.id):
        await bot.reply_to(
            message,
            f"*User ID:* {message.from_user.id}\n*Username:* {message.from_user.username}\n*Full Name:* {message.from_user.full_name}",
            parse_mode="Markdown"
        )
#===========
@bot.message_handler(commands=['chatinfo'])
async def chatinfo(message: Message):
    """Gets the chat info"""
    if isadmin(message.from_user.id):
        await bot.reply_to(
            message,
            f"*Chat ID:* {message.chat.id}\n*Chat Title:* {message.chat.title}\n*Chat Type:* {message.chat.type}",
            parse_mode="Markdown"
        )