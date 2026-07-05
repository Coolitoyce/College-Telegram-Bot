from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

#===============
# Year 1 Semester 1
year1_sem1_markup = InlineKeyboardMarkup()
year1_sem1_markup.row(
    InlineKeyboardButton(
        "👨🏻‍💻 Intro to Programming",
        callback_data="course:1"
    )
)
year1_sem1_markup.row(
    InlineKeyboardButton(
        "💻 Intro to Computing",
        callback_data="course:2"
    )
)
year1_sem1_markup.row(
    InlineKeyboardButton(
        "💡 Electronics",
        callback_data="course:3"
    )
)
year1_sem1_markup.row(
    InlineKeyboardButton(
        "🔢 Math 1",
        callback_data="course:4"
    )
)
year1_sem1_markup.row(
    InlineKeyboardButton(
        "⚛️ Physics",
        callback_data="course:5"
    )
)
year1_sem1_markup.row(
    InlineKeyboardButton(
        "✍️ English",
        callback_data="course:6"
    )
)
year1_sem1_markup.row(
    InlineKeyboardButton(
        "🗣 Communication Skills",
        callback_data="course:7"
    )
)
year1_sem1_markup.row(
    InlineKeyboardButton(
        "➗ Math 0",
        callback_data="course:28"
    )
)
year1_sem1_markup.row(
    InlineKeyboardButton(
        "القائمة الرئيسية 🔝",
        callback_data="home",
        style="primary"
    ),
    InlineKeyboardButton(
        "رجوع 🔙",
        callback_data="year:1",
        style="primary"
    )
)

#===============
# Year 1 Semester 2
year1_sem2_markup = InlineKeyboardMarkup()
year1_sem2_markup.row(
    InlineKeyboardButton(
        "👨🏻‍💻 OOP",
        callback_data="course:8"
    )
)
year1_sem2_markup.row(
    InlineKeyboardButton(
        "🌐 Intro to Web Programming",
        callback_data="course:9"
    )
)
year1_sem2_markup.row(
    InlineKeyboardButton(
        "🔌 Digital Logic Circuits",
        callback_data="course:10"
    )
)
year1_sem2_markup.row(
    InlineKeyboardButton(
        "📊 Probability & Statistics",
        callback_data="course:11"
    )
)
year1_sem2_markup.row(
    InlineKeyboardButton(
        "🔢 Math 2",
        callback_data="course:12"
    )
)
year1_sem2_markup.row(
    InlineKeyboardButton(
        "💼 Technological Entrepreneurship",
        callback_data="course:13"
    )
)
year1_sem2_markup.row(
    InlineKeyboardButton(
        "القضايا المجتمعية 👥",
        callback_data="course:14"
    )
)
year1_sem2_markup.row(
    InlineKeyboardButton(
        "القائمة الرئيسية 🔝",
        callback_data="home",
        style="primary"
    ),
    InlineKeyboardButton(
        "رجوع 🔙",
        callback_data="year:1",
        style="primary"
    )
)


#===============
# Year 1 Semester 1
year2_sem1_markup = InlineKeyboardMarkup()
year2_sem1_markup.row(
    InlineKeyboardButton(
        "🧩 Data Structures & Algorithms",
        callback_data="course:15"
    )
)
year2_sem1_markup.row(
    InlineKeyboardButton(
        "💻 Computer Architecture",
        callback_data="course:16"
    )
)

year2_sem1_markup.row(
    InlineKeyboardButton(
        "👨🏻‍💻 Software Engineering",
        callback_data="course:17"
    )
)
year2_sem1_markup.row(
    InlineKeyboardButton(
        "🌐 Data Communications",
        callback_data="course:18"
    )
)
year2_sem1_markup.row(
    InlineKeyboardButton(
        "🔢 Linear Algebra",
        callback_data="course:20"
    )
)
year2_sem1_markup.row(
    InlineKeyboardButton(
        "🧮 Discrete Math",
        callback_data="course:19"
    )
)
year2_sem1_markup.row(
    InlineKeyboardButton(
        "القائمة الرئيسية 🔝",
        callback_data="home",
        style="primary"
    ),
    InlineKeyboardButton(
        "رجوع 🔙",
        callback_data="year:2",
        style="primary"
    )
)

#===============
# Year 2 Semester 2
year2_sem2_markup = InlineKeyboardMarkup()
year2_sem2_markup.row(
    InlineKeyboardButton(
        "🖥 Operating Systems",
        callback_data="course:21"
    )
)
year2_sem2_markup.row(
    InlineKeyboardButton(
        "🧠 AI Fundamentals",
        callback_data="course:22"
    )
)
year2_sem2_markup.row(
    InlineKeyboardButton(
        "🗄 Database Systems",
        callback_data="course:23"
    )
)
year2_sem2_markup.row(
    InlineKeyboardButton(
        "📈 Data Analysis",
        callback_data="course:24"
    )
)
year2_sem2_markup.row(
    InlineKeyboardButton(
        "🌐 Computer Networks",
        callback_data="course:25"
    )
)
year2_sem2_markup.row(
    InlineKeyboardButton(
        "📝 Technical Writing",
        callback_data="course:26"
    )
)
year2_sem2_markup.row(
    InlineKeyboardButton(
        "الدراسات القانونية ⚖️",
        callback_data="course:27"
    )
)
year2_sem2_markup.row(
    InlineKeyboardButton(
        "القائمة الرئيسية 🔝",
        callback_data="home",
        style="primary"
    ),
    InlineKeyboardButton(
        "رجوع 🔙",
        callback_data="year:2",
        style="primary"
    )
)

#===============