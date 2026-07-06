from config import bot, LOGS_GROUP, ADMIN_ID
from telebot.types import Message
import logging
import database
#===========
logger = logging.getLogger("coolig_bot")

#===========
async def log_to_group(msg: str):
    """Sends a message to the logs group chat"""
    try:
        await bot.send_message(
            LOGS_GROUP,
            text=msg
        )
    except Exception as e:
        logger.error(f"Failed to log to group: {e}")

#===========
def isadmin(id: int) -> bool:
    """Checks if the user is an admin"""
    if id == ADMIN_ID:
        return True      
    return False

#===========
@bot.message_handler(commands=['get_file'])
async def add_material(message: Message):
    """Sends a file from a given ID"""
    if isadmin(message.from_user.id):
        args = message.text.split(maxsplit=1)
        if len(args) != 2:
            return await bot.reply_to(message, "*Usage:*\n`/get_file <FILEID>`", parse_mode="Markdown")

        file_id = args[1]
        try:
            await bot.send_document(message.chat.id, file_id)

        except Exception as e:
            print(e)
            return await bot.reply_to(message, "A file with that ID doesn't exist.")


#===========
@bot.message_handler(content_types=['document', 'video', 'photo'])
async def add_material(message: Message):
    """Adds a new material to the database"""
    if message.content_type == "video":
        file_id = message.video.file_id
        file_name = message.video.file_name
    elif message.content_type == "photo":
        file_id = message.photo.file_id
        file_name = message.photo.file_name              
    else:
        file_id = message.document.file_id
        file_name = message.document.file_name

    if isadmin(message.from_user.id):
        if message.caption is not None and message.caption.startswith('/add_material'):
            args = message.caption.split(maxsplit=1) 
            if len(args) != 2 or message.caption is None:
                return await bot.reply_to(
                    message,
                    "*Usage:*\n`/add_material <Course_ID>|<Type>`",
                    parse_mode="Markdown"
                )
            args = args[1].split(sep='|')
            if len(args) != 2:
                return await bot.reply_to(
                    message,
                    "❌ *Incorrect Arguments*\n*Usage:*\n`/add_material <Course_ID>|<Type>`",
                )
            course_id = int(args[0])
            material_type = args[1].strip().lower() 

            try:
                await database.add_material(course_id, file_name, material_type, file_id)
                await log_to_group(f"Added a new material with: course id={course_id}, file name={file_name}, material type={material_type}")
                await bot.reply_to(message, "Got it! Material added successfully.")

            except Exception as e:
                logger.error(f"Failed to add material: {e}")
                await log_to_group(f"Failed to add material: {e}")
                return await bot.reply_to(message, "❌ Failed to add material.")

        else:
            await bot.reply_to(
                message,
                f"*Got it!*\n*File ID:*\n`{file_id}`",
                parse_mode="Markdown"
            )          
            logger.info(f"Got file {file_name} with ID: {file_id}")
            await log_to_group(f"Got file {file_name} with ID: {file_id}")
    else:
        await bot.reply_to(
            message,
            f"*لسه مضفتش ميزة أنك ترفع الماتريال بتاعتك للبوت 🙃*\n*لإعادة تحميل القائمة اضغط /start*."
        )
        
        logger.info(f"User {message.from_user.id}({message.from_user.username}) tried sending a file with name={file_name}, ID={file_id}")
        await log_to_group(f"User {message.from_user.id}({message.from_user.username}) tried sending this file:")
        await bot.forward_message(
            LOGS_GROUP,
            message.chat.id,
            message.id
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
                "*Usage:*\n`/add_resource <Course_ID>|<Title>|<URL>`",
                parse_mode="Markdown"
            )
        args = args[1].split(sep='|')
        if len(args) != 3:
            return await bot.reply_to(
                message,
                "❌ *Incorrect Arguments*\n*Usage:*\n`/add_resource <Course_ID>|<Title>|<URL>`",
            )
        course_id = int(args[0])
        title = args[1].strip()
        url = args[2].strip()
        
        try:
            await database.add_resource(course_id, title, url)
            await log_to_group(f"Added a new resource with: course_id={course_id}, title={title}, url={url}")
            await bot.reply_to(message, "Resource added successfully.")

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
        dept = args[3].strip() if len(args) == 4 else None
        
        try:
            await database.add_course(course_name, year, sem, dept)
            await log_to_group(f"Added a new course with: name={course_name}, year={year}, semester={sem}, department={dept}")
            await bot.reply_to(message, "Course added successfully.")

        except Exception as e:
            logger.error(f"Failed to add course: {e}")
            await log_to_group(f"Failed to add course: {e}")
            return await bot.reply_to(message, "❌ Failed to add the course.")


#===========
@bot.message_handler(commands=['get_courses'])
async def get_courses(message: Message):
    """Gets courses in the database"""
    if isadmin(message.from_user.id):
        args = message.text.split(maxsplit=2)
        year = None
        semeseter = None
        if len(args) == 2:
            year = int(args[1])

        elif len(args) == 3:
            year = int(args[1])
            semeseter = int(args[2])
        
        reply_msg = ""
        if semeseter:
            courses = await database.get_courses(year, semeseter) # courses = (id, name, year, sem, dept)
            reply_msg += f"\n<b>Year {year}, Semester {semeseter} Courses</b>\n<blockquote>"
            for course in courses: 
                reply_msg += f"<b>{course[1]}</b>\nID: {course[0]}\nDepartment: {course[4]}\n\n"
            
            reply_msg += "</blockquote>"

        elif year:
            courses = await database.get_courses(year=year)
            reply_msg += f"\n<b>Year {year} Courses</b>\n<blockquote>"
            for course in courses: 
                reply_msg += f"<b>{course[1]}</b>\nID: {course[0]}\nSemester: {course[3]}\nDepartment: {course[4]}\n\n"

            reply_msg += "</blockquote>"

        else:
            courses = await database.get_courses() 
            for i in range(1, 5):
                reply_msg += f"=====\n<b>Year {i} Courses</b>\n<blockquote>"
                found_course = False
                for course in courses: 
                    if course[2] == i:
                        found_course = True
                        reply_msg += f"<b>{course[1]}</b>\nID: {course[0]}\nSemester: {course[3]}\nDepartment: {course[4]}\n\n"

                if not found_course:
                    reply_msg += "</blockquote>\n"
                else:
                    reply_msg += "</blockquote>"
        
        await bot.reply_to(message, reply_msg, parse_mode="HTML")


#===========
@bot.message_handler(commands=['get_materials'])
async def get_materials(message: Message):
    """Gets materials in the database"""
    if isadmin(message.from_user.id):
        args = message.text.split()
        course_id = None
        if len(args) == 3:
            course_id = int(args[1])
            material_type = args[2]

        elif len(args) == 2:
            course_id = int(args[1])

        reply_msg = ""
        if material_type:
            materials = await database.get_materials(course_id, material_type) # materials = (id, course_id, title, type, telegram_file_id, uploaded_at)
            reply_msg += f"\n<b>Course {course_id} Materials of Type {material_type}</b>\n<blockquote>"
            for material in materials: 
                reply_msg += f"<b>{material[2]}</b>\nID: {material[0]}\nTelegram File ID: {material[4]}\nUploaded at: {material[5]}\n\n"

            reply_msg += "</blockquote>"

        elif course_id:
            materials = await database.get_materials(course_id) 
            reply_msg += f"\n<b>Course {course_id} Materials</b>\n<blockquote>"
            for material in materials: 
                reply_msg += f"<b>{material[2]}</b>\nID: {material[0]}\nType: {material[3]}\nTelegram File ID: {material[4]}\nUploaded at: {material[5]}\n\n"

            reply_msg += "</blockquote>"

        else:
            max_course_id = -1
            for x in materials:
                if x[1] > max_course_id:
                    max_course_id = x[1]

            for i in range(1, max_course_id + 1):
                reply_msg += f"=====\n<b>Course {i} Materials</b>\n<blockquote>"
                found_material = False
                for material in materials: 
                    if material[1] == i:
                        found_material = True
                        reply_msg += f"<b>{material[2]}</b>\nID: {material[0]}\nType: {material[3]}\nTelegram File ID: {material[4]}\nUploaded at: {material[5]}\n\n"

                if not found_material:
                    reply_msg += "</blockquote>\n"
                else:
                    reply_msg += "</blockquote>"
        
        await bot.reply_to(message, reply_msg, parse_mode="HTML")


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
            reply_msg += f"\n<b>Course {course_id} Resources</b>\n<blockquote>"
            for resource in resources: 
                reply_msg += f"<b>{resource[2]}</b>\nID: {resource[0]}\nURL: {resource[3]}\nUploaded at: {resource[4]}\n\n"

            reply_msg += "</blockquote>"

        else:
            max_course_id = -1
            for x in resources:
                if x[1] > max_course_id:
                    max_course_id = x[1]

            for i in range(1, max_course_id + 1):
                reply_msg += f"=====\n<b>Course {i} Resources</b>\n<blockquote>"
                found_resource = False
                for resource in resources: 
                    if resource[1] == i:
                        found_resource = True
                        reply_msg += f"<b>{resource[2]}</b>\nID: {resource[0]}\nURL: {resource[3]}\nUploaded at: {resource[4]}\n\n"

                if not found_resource:
                    reply_msg += "</blockquote>\n"
                else:
                    reply_msg += "</blockquote>"
        
        await bot.reply_to(message, reply_msg, parse_mode="HTML")


#===========
@bot.message_handler(commands=['id'])
async def get_chatid(message: Message):
    """Gets the current chat ID"""
    if isadmin(message.from_user.id):
        await bot.reply_to(message, f"Chat ID: {message.chat.id}\nChat Title: {message.chat.title}")