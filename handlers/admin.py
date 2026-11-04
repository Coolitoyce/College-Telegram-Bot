from config import bot, log_to_group, ADMIN_ID
from telebot.types import Message
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

#===========
# Command to list all admin commands and their correct usages
@bot.message_handler(commands=['admin_help'])
async def admin_help(message: Message):
    """Sends a list of all admin commands and their correct usages"""
    if isadmin(message.from_user.id):
        help_text = (
            "<b>Admin Commands:</b>\n\n"
            "<blockquote>"
            "<code>/admin</code> - Opens the admin panel (browse, rename, move, delete, upload).\n"
            "<code>/admin_help</code> - Shows this help message.\n"
            "<code>/userinfo</code> - Gets the current user's info.\n"
            "<code>/chatinfo</code> - Gets the current chat's info.\n"
            "<code>/add_material [CourseID] [Type]</code> - Starts/ends upload mode (no args = choose with buttons).\n"
            "<code>/cancel</code> - Cancels a pending admin text input.\n"
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
        args = args[1].split(sep='|')
        if len(args) != 3:
            return await bot.reply_to(
                message,
                "❌ *Incorrect Arguments*\n*Usage:*\n`/add_resource <CourseID>|<Title>|<URL>`",
            )
        course_id = int(args[0])
        title = args[1].strip()
        url = args[2].strip()
        
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
        
        args = args[1].split(sep='|')
        if len(args) not in (3, 4):
            return await bot.reply_to(
                message,
                "❌ *Incorrect Arguments*\n*Usage:*\n`/add_course <Course Name>|<Year>|<Semester>|<Department>`",
            )
        
        course_name = args[0].strip()
        year = int(args[1])
        sem = int(args[2])
        dept = args[3].strip().upper() if len(args) == 4 else None
        
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
        
        try:
            course_id = int(args[1])
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
        
        try:
            resource_id = int(args[1])
            await database.remove_resource(resource_id)
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
        
        try:
            material_id = int(args[1])
            await database.remove_material(material_id)
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
            year = int(args[1])

        elif len(args) == 3:
            year = int(args[1])
            semeseter = int(args[2])
        
        elif len(args) == 4:
            year = int(args[1])
            semeseter = int(args[2])
            dept = args[3].upper()
        
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
            course_id = int(args[1])
            print(f"course id = {course_id}")
            material_type = args[2]
            print(f"material_type id = {material_type}")

        elif len(args) == 2:
            course_id = int(args[1])
            print(f"course id = {course_id}")

        reply_msg = ""
        if material_type:
            materials = await database.get_materials(course_id, material_type) # materials = (id, course_id, title, type, telegram_file_id, uploaded_at)
            reply_msg += f"\n<b>Course {course_id} Materials of Type {material_type}</b>\n<blockquote expandable>"
            for material in materials: 
                reply_msg += f"<b>{material[2]}</b>\nID: {material[0]}\nTelegram File ID: {material[4]}\nUploaded at: {material[5]}\n\n"

            reply_msg += "</blockquote>"

        elif course_id:
            materials = await database.get_materials(course_id) 
            reply_msg += f"\n<b>Course {course_id} Materials</b>\n<blockquote expandable>"
            for material in materials: 
                reply_msg += f"<b>{material[2]}</b>\nID: {material[0]}\nType: {material[3]}\nTelegram File ID: {material[4]}\nUploaded at: {material[5]}\n\n"

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
            course_id = int(args[1])

        reply_msg = ""
        if course_id:
            resources = await database.get_resources(course_id) # resources = (id, course_id, title, url, uploaded_at)
            reply_msg += f"\n<b>Course {course_id} Resources</b>\n<blockquote expandable>"
            for resource in resources: 
                reply_msg += f"<b>{resource[2]}</b>\nID: {resource[0]}\nURL: {resource[3]}\nUploaded at: {resource[4]}\n\n"

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