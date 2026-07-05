import aiosqlite
import logging
#=====================
logger = logging.getLogger("coolig_bot")

#=====================
async def ready_tables():
    """Creates/Prepares Tables"""
    async with aiosqlite.connect("database.db") as db:
        await db.execute(
            """CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                year INTEGER NOT NULL,
                semester INTEGER NOT NULL,
                department TEXT
            )"""
        )

        await db.execute(
            """CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                telegram_file_id TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (course_id) REFERENCES courses(id)
            )"""
        )

        await db.execute(
            """CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (course_id) REFERENCES courses(id)

            )"""
        )

        await db.commit()


#=====================
async def add_course(name: str, year: int, sem: int, dept: str = None):
    """Adds a new course to the database"""
    async with aiosqlite.connect("database.db") as db:
        await db.execute(
            """INSERT INTO courses (name, year, semester, department)
            VALUES (?, ?, ?, ?)""", (name, year, sem, dept)
        )
        await db.commit()
        logger.info(f"Added a new course with: name={name}, year={year}, semester={sem}, department={dept}")


#=====================
async def get_course_name(course_id: int):
    """Gets a course name from its ID"""
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT name FROM courses WHERE id = ?", (course_id,)) as cursor:
            row = await cursor.fetchone()

    return row[0] if row else None


#=====================
async def get_courses(year: int = None, semester: int = None):
    """Get all courses in the database"""
    async with aiosqlite.connect("database.db") as db:
        db.row_factory = aiosqlite.Row
        courses = []
        if semester:
            async with db.execute("SELECT * FROM courses WHERE year = ? AND semester = ? ORDER BY year, semester", (year, semester)) as cursor:
                async for row in cursor:
                    courses.append((row['id'], row['name'], row['year'], row['semester'], row['department']))            
        elif year:
            async with db.execute("SELECT * FROM courses WHERE year = ? ORDER BY year, semester", (year, )) as cursor:
                async for row in cursor:
                    courses.append((row['id'], row['name'], row['year'], row['semester'], row['department']))
        
        else:
            async with db.execute("SELECT * FROM courses ORDER BY year, semester") as cursor:
                async for row in cursor:
                    courses.append((row['id'], row['name'], row['year'], row['semester'], row['department']))

    return courses    


#=====================
async def add_material(course_id: int, title: str, material_type: str, file_id: str):
    """Adds a new material to the database"""
    async with aiosqlite.connect("database.db") as db:
        await db.execute(
            """INSERT INTO materials (course_id, title, type, telegram_file_id)
            VALUES (?, ?, ?, ?)""", (course_id, title, material_type, file_id)
        )

        await db.commit()
        logger.info(f"Added a new material with: course id={course_id}, file name={title}, material type={material_type}, file id={file_id}")


#=====================
async def get_materials(course_id: int = None, material_type: str = None):
    """Gets all materials in the database"""
    async with aiosqlite.connect("database.db") as db:
        db.row_factory = aiosqlite.Row
        materials = []
        if material_type:
            async with db.execute("SELECT * FROM materials WHERE course_id = ? AND type = ? ORDER BY title", (course_id, material_type)) as cursor:
                async for row in cursor:
                    materials.append((row['id'], row['course_id'], row['title'], row['type'], row['telegram_file_id'], row['uploaded_at']))

        elif course_id:
            async with db.execute("SELECT * FROM materials WHERE course_id = ? ORDER BY title", (course_id, )) as cursor:
                async for row in cursor:
                    materials.append((row['id'], row['course_id'], row['title'], row['type'], row['telegram_file_id'], row['uploaded_at']))

        else:
            async with db.execute("SELECT * FROM materials ORDER BY course_id, title") as cursor:
                async for row in cursor:
                    materials.append((row['id'], row['course_id'], row['title'], row['type'], row['telegram_file_id'], row['uploaded_at']))

    return materials    


#=====================
async def add_resource(course_id: int, title: str, url: str):
    """Adds a new resource to the database"""
    async with aiosqlite.connect("database.db") as db:
        await db.execute(
            """INSERT INTO resources (course_id, title, url)
            VALUES (?, ?, ?)""", (course_id, title, url)
        )
        await db.commit()
        logger.info(f"Added a new resource with: course_id={course_id}, title={title}, url={url}")


#=====================
async def get_resources(course_id: int = None):
    """Gets all materials in the database"""
    async with aiosqlite.connect("database.db") as db:
        db.row_factory = aiosqlite.Row
        resources = []
        if course_id:
            async with db.execute("SELECT * FROM resources WHERE course_id = ? ORDER BY title", (course_id, )) as cursor:
                async for row in cursor:
                    resources.append((row['id'], row['course_id'], row['title'], row['url'], row['uploaded_at']))
        else:
            async with db.execute("SELECT * FROM resources ORDER BY course_id, title") as cursor:
                async for row in cursor:
                    resources.append((row['id'], row['course_id'], row['title'], row['url'], row['uploaded_at']))

    
    return resources


#=====================