from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

#===========
# Years Keyboard
year_markup = InlineKeyboardMarkup()
year_markup.row(
    InlineKeyboardButton(
        "المستوى الثاني 2️⃣",
        callback_data="year:2"
    ),
    InlineKeyboardButton(
        "المستوى الأول 1️⃣",
        callback_data="year:1"
    )

)
year_markup.row(
    InlineKeyboardButton(
        "المستوى الرابع 4️⃣",
        callback_data="year:4"
    ),
    InlineKeyboardButton(
        "المستوى الثالث 3️⃣",
        callback_data="year:3"
    )
)

#===========
# Semesters Keyboard
semester_markup = InlineKeyboardMarkup()
semester_markup.row(
    InlineKeyboardButton(
        "الترم الثاني",
        callback_data="sem:2"
    ),
    InlineKeyboardButton(
        "الترم الأول",
        callback_data="sem:1"
    )
)
semester_markup.row(
    InlineKeyboardButton(
        "القائمة الرئيسية 🔝",
        callback_data="home",
        style="primary"
    ),
    InlineKeyboardButton(
        "رجوع 🔙",
        callback_data="home",
        style="primary"
    )
)

#===========
# Departments Keyboard
dept_markup = InlineKeyboardMarkup()
dept_markup.row(
    InlineKeyboardButton(
        "📊 IS",
        callback_data="dept:is"
    ),
    InlineKeyboardButton(
        "🌐 IT",
        callback_data="dept:it"
    ),
    InlineKeyboardButton(
        "💻 CS",
        callback_data="dept:cs"
    )
)
dept_markup.row(
    InlineKeyboardButton(
        "القائمة الرئيسية 🔝",
        callback_data="home",
        style="primary"
    ),
    InlineKeyboardButton(
        "رجوع 🔙",
        callback_data="home",
        style="primary"
    )
)


#===========
# Back Keyboard
back_markup = InlineKeyboardMarkup()
back_markup.row(
    InlineKeyboardButton(
        "القائمة الرئيسية 🔝",
        callback_data="home",
        style="primary"
    ),
    InlineKeyboardButton(
        "رجوع 🔙",
        callback_data="home",
        style="primary"
    )
)

#===========
# Contribute Keyboard
contribute_markup = InlineKeyboardMarkup()
contribute_markup.row(
    InlineKeyboardButton(
        "📄 Files",
        callback_data="send:doc"
    ),
    InlineKeyboardButton(
        "▶️ Video links",
        callback_data="send:link"
    )
)

#===========
# End Contribute Keyboard
end_contribute_markup = InlineKeyboardMarkup()
end_contribute_markup.row(
    InlineKeyboardButton(
        "انهاء ✅",
        style="primary",
        callback_data="finish_send"
    ),
)
#===========
# Cancel Contribute Keyboard (For links)
cancel_contribute_markup = InlineKeyboardMarkup()
cancel_contribute_markup.row(
    InlineKeyboardButton(
        "الغاء ❌",
        style="primary",
        callback_data="cancel_send"
    ),
)

#===========
# Contribute Description Keyboard
description_markup = InlineKeyboardMarkup()
description_markup.row(
    InlineKeyboardButton(
        "📝 Description",
        style="primary",
        callback_data="description"
    )
)

#===========
# Cancel Description Keyboard
cancel_desc_markup = InlineKeyboardMarkup()
cancel_desc_markup.row(
    InlineKeyboardButton(
        "الغاء ❌",
        style="primary",
        callback_data="cancel_description"
    )
)