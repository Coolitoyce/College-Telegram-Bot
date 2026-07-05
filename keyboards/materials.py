from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# material_types = ["lecture", "section", "summary", "practical", "exam", "book"]
#===============
# Materials Keyboard
def materials_markup(semester: int):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(
            "كتاب 📘",
            callback_data="material:book"
        )
    )
    markup.row(
        InlineKeyboardButton(
            "سكاشن 👥",
            callback_data="material:section"
        ),
        InlineKeyboardButton(
            "محاضرات 📚",
            callback_data="material:lecture"
        )
    )
    markup.row(
        InlineKeyboardButton(
            "ملخصات 📝",
            callback_data="material:summary"
        ),
        InlineKeyboardButton(
            "فيديوهات ▶️",
            callback_data="resource"
        )
    )
    markup.row(
        InlineKeyboardButton(
            "امتحانات 📋",
            callback_data="material:exam"
        ),
        InlineKeyboardButton(
            "عملي 💻",
            callback_data="material:practical"
        )
    )
    markup.row(
        InlineKeyboardButton(
            "القائمة الرئيسية 🔝",
            callback_data="home",
            style="primary"
        ),
        InlineKeyboardButton(
            "رجوع 🔙",
            callback_data=f"sem:{semester}",
            style="primary"
        )
    )
    
    return markup


#===========
# Vidoes Keyboard
def resources_markup(course_id: int, resources: list[tuple[str, str]]):
    markup = InlineKeyboardMarkup()
    
    for text, url in resources:
        markup.row(
            InlineKeyboardButton(
                f"▶️ {text}",
                url=url
            )
        )

    markup.row(
        InlineKeyboardButton(
            "القائمة الرئيسية 🔝",
            callback_data="home",
            style="primary"
        ),
        InlineKeyboardButton(
            "رجوع 🔙",
            callback_data=f"course:{course_id}",
            style="primary"
        )
    )

    return markup


#===========
# Back Keyboard based on Course
def back_markup(course_id: int):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(
            "القائمة الرئيسية 🔝",
            callback_data="home",
            style="primary"
        ),
        InlineKeyboardButton(
            "رجوع 🔙",
            callback_data=f"course:{course_id}",
            style="primary"
        )
    )

    return markup


#===========