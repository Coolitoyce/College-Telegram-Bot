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
# Year 2 Semester 1
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
# Year 3 Semester 1 CS Department
year3_sem1_cs_markup = InlineKeyboardMarkup()
year3_sem1_cs_markup.row(
    InlineKeyboardButton(
        "🧮 Algorithms Design and Analysis",
        callback_data="course:30"
    )
)
year3_sem1_cs_markup.row(
    InlineKeyboardButton(
        "💾 Microprocessors",
        callback_data="course:29"
    )
)
year3_sem1_cs_markup.row(
    InlineKeyboardButton(
        "🤖 Machine Learning",
        callback_data="course:31"
    )
)
year3_sem1_cs_markup.row(
    InlineKeyboardButton(
        "🔍 Software Testing",
        callback_data="course:32"
    )
)
year3_sem1_cs_markup.row(
    InlineKeyboardButton(
        "🧠 Soft Computing",
        callback_data="course:33"
    )
)
year3_sem1_cs_markup.row(
    InlineKeyboardButton(
        "🌐 Distributed Systems",
        callback_data="course:34"
    )
)

year3_sem1_cs_markup.row(
    InlineKeyboardButton(
        "القائمة الرئيسية 🔝",
        callback_data="home",
        style="primary"
    ),
    InlineKeyboardButton(
        "رجوع 🔙",
        callback_data="dept:cs",
        style="primary"
    )
)

#===============
# Year 3 Semester 1 IT Department
year3_sem1_it_markup = InlineKeyboardMarkup()
year3_sem1_it_markup.row(
    InlineKeyboardButton(
        "🧮 Algorithms Design and Analysis",
        callback_data="course:30"
    )
)
year3_sem1_it_markup.row(
    InlineKeyboardButton(
        "💾 Microprocessors",
        callback_data="course:29"
    )
)
year3_sem1_it_markup.row(
    InlineKeyboardButton(
        "📡 Digital Signal Processing",
        callback_data="course:35"
    )
)
year3_sem1_it_markup.row(
    InlineKeyboardButton(
        "🔍 Pattern Recognition",
        callback_data="course:36"
    )
)
year3_sem1_it_markup.row(
    InlineKeyboardButton(
        "🎨 Computer Graphics",
        callback_data="course:37"
    )
)
year3_sem1_it_markup.row(
    InlineKeyboardButton(
        "📶 Wireless and Sensor Networks",
        callback_data="course:38"
    )
)

year3_sem1_it_markup.row(
    InlineKeyboardButton(
        "القائمة الرئيسية 🔝",
        callback_data="home",
        style="primary"
    ),
    InlineKeyboardButton(
        "رجوع 🔙",
        callback_data="dept:it",
        style="primary"
    )
)

#===============
# Year 3 Semester 1 IS Department
year3_sem1_is_markup = InlineKeyboardMarkup()
year3_sem1_is_markup.row(
    InlineKeyboardButton(
        "🧮 Algorithms Design and Analysis",
        callback_data="course:30"
    )
)
year3_sem1_is_markup.row(
    InlineKeyboardButton(
        "📋 Project Management",
        callback_data="course:39"
    )
)
year3_sem1_is_markup.row(
    InlineKeyboardButton(
        "🏗️ System Analysis and Design",
        callback_data="course:40"
    )
)
year3_sem1_is_markup.row(
    InlineKeyboardButton(
        "🗄️ Advanced Database",
        callback_data="course:41"
    )
)
year3_sem1_is_markup.row(
    InlineKeyboardButton(
        "📊 Business Intelligent System",
        callback_data="course:42"
    )
)
year3_sem1_is_markup.row(
    InlineKeyboardButton(
        "🧠 Decision Support System",
        callback_data="course:43"
    )
)

year3_sem1_is_markup.row(
    InlineKeyboardButton(
        "القائمة الرئيسية 🔝",
        callback_data="home",
        style="primary"
    ),
    InlineKeyboardButton(
        "رجوع 🔙",
        callback_data="dept:is",
        style="primary"
    )
)

#===============
# Year 3 Semester 2 CS Department
year3_sem2_cs_markup = InlineKeyboardMarkup()
year3_sem2_cs_markup.row(
    InlineKeyboardButton(
        "🧠 Deep Learning",
        callback_data="course:44"
    )
)
year3_sem2_cs_markup.row(
    InlineKeyboardButton(
        "🩺 Biomedical Informatics",
        callback_data="course:46"
    )
)
year3_sem2_cs_markup.row(
    InlineKeyboardButton(
        "🧬 Bioinformatics",
        callback_data="course:47"
    )
)
year3_sem2_cs_markup.row(
    InlineKeyboardButton(
        "🖥️ Human Computer Interaction",
        callback_data="course:48"
    )
)
year3_sem2_cs_markup.row(
    InlineKeyboardButton(
        "القائمة الرئيسية 🔝",
        callback_data="home",
        style="primary"
    ),
    InlineKeyboardButton(
        "رجوع 🔙",
        callback_data="dept:cs",
        style="primary"
    )
)

#===============
# Year 3 Semester 2 IT Department
year3_sem2_it_markup = InlineKeyboardMarkup()
year3_sem2_it_markup.row(
    InlineKeyboardButton(
        "🌐 Network Analysis",
        callback_data="course:49"
    )
)
year3_sem2_it_markup.row(
    InlineKeyboardButton(
        "🖼️ Digital Image Processing",
        callback_data="course:50"
    )
)
year3_sem2_it_markup.row(
    InlineKeyboardButton(
        "🔌 Network Programming",
        callback_data="course:51"
    )
)
year3_sem2_it_markup.row(
    InlineKeyboardButton(
        "🔐 Cryptography",
        callback_data="course:52"
    )
)
year3_sem2_it_markup.row(
    InlineKeyboardButton(
        "القائمة الرئيسية 🔝",
        callback_data="home",
        style="primary"
    ),
    InlineKeyboardButton(
        "رجوع 🔙",
        callback_data="dept:it",
        style="primary"
    )
)

#===============
# Year 3 Semester 2 IS Department
year3_sem2_is_markup = InlineKeyboardMarkup()
year3_sem2_is_markup.row(
    InlineKeyboardButton(
        "📊 Data Visualization",
        callback_data="course:53"
    )
)
year3_sem2_is_markup.row(
    InlineKeyboardButton(
        "🔍 Information Storage and Retrieval",
        callback_data="course:54"
    )
)
year3_sem2_is_markup.row(
    InlineKeyboardButton(
        "⛏️ Data Mining",
        callback_data="course:55"
    )
)
year3_sem2_is_markup.row(
    InlineKeyboardButton(
        "🏭 Data Warehouse",
        callback_data="course:56"
    )
)

year3_sem2_is_markup.row(
    InlineKeyboardButton(
        "القائمة الرئيسية 🔝",
        callback_data="home",
        style="primary"
    ),
    InlineKeyboardButton(
        "رجوع 🔙",
        callback_data="dept:is",
        style="primary"
    )
)