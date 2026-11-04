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

        await db.execute(
            """CREATE TABLE IF NOT EXISTS contribution_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_label TEXT,
                description TEXT,
                card_chat_id INTEGER,
                card_message_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )

        await db.execute(
            """CREATE TABLE IF NOT EXISTS contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER,
                user_id INTEGER NOT NULL,
                user_label TEXT,
                kind TEXT NOT NULL,              -- 'file' or 'link'
                file_id TEXT,
                media TEXT,                      -- 'document', 'photo' or 'video'
                file_name TEXT,
                urls TEXT,                       -- newline separated (links only)
                status TEXT NOT NULL DEFAULT 'pending',  -- pending/approved/rejected
                card_chat_id INTEGER,
                card_message_id INTEGER,
                reviewed_by INTEGER,
                reviewed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )

        # Migration: remember how each material must be sent (document/photo/video)
        async with db.execute("PRAGMA table_info(materials)") as cursor:
            columns = [row[1] async for row in cursor]
        if "media" not in columns:
            await db.execute("ALTER TABLE materials ADD COLUMN media TEXT NOT NULL DEFAULT 'document'")
            logger.info("Migrated materials table: added media column.")

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
async def remove_course(course_id: int):
    """Removes a course from the database"""
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute(
            "DELETE FROM courses WHERE id = ?", (course_id,)
        )
        await db.commit()
        if cursor.rowcount == 0:
            logger.warning(f"Attempted to remove course with ID: {course_id}, but it does not exist.")
            return False

        logger.info(f"Removed course with ID: {course_id}")
        return True


#=====================
async def get_course_name(course_id: int):
    """Gets a course name from its ID"""
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT name FROM courses WHERE id = ?", (course_id,)) as cursor:
            row = await cursor.fetchone()

    return row[0] if row else None


#=====================
async def get_courses(year: int = None, semester: int = None, dept: str = None):
    """Get all courses in the database"""
    async with aiosqlite.connect("database.db") as db:
        db.row_factory = aiosqlite.Row
        courses = []
        if dept:
            async with db.execute("SELECT * FROM courses WHERE year = ? AND semester = ? AND department = ? ORDER BY year, semester", (year, semester, dept)) as cursor:
                async for row in cursor:
                    courses.append((row['id'], row['name'], row['year'], row['semester'], row['department']))
        elif semester:
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
async def add_material(course_id: int, title: str, material_type: str, file_id: str, media: str = "document"):
    """Adds a new material to the database and returns its ID"""
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute(
            """INSERT INTO materials (course_id, title, type, telegram_file_id, media)
            VALUES (?, ?, ?, ?, ?)""", (course_id, title, material_type, file_id, media)
        )

        await db.commit()
        logger.info(f"Added a new material with: course id={course_id}, file name={title}, material type={material_type}, media={media}, file id={file_id}")
        return cursor.lastrowid


#=====================
async def get_materials(course_id: int = None, material_type: str = None):
    """Gets all materials in the database"""
    async with aiosqlite.connect("database.db") as db:
        db.row_factory = aiosqlite.Row
        materials = []
        if material_type:
            async with db.execute("SELECT * FROM materials WHERE course_id = ? AND type = ? ORDER BY title", (course_id, material_type)) as cursor:
                async for row in cursor:
                    materials.append((row['id'], row['course_id'], row['title'], row['type'], row['telegram_file_id'], row['uploaded_at'], row['media']))

        elif course_id:
            async with db.execute("SELECT * FROM materials WHERE course_id = ? ORDER BY title", (course_id, )) as cursor:
                async for row in cursor:
                    materials.append((row['id'], row['course_id'], row['title'], row['type'], row['telegram_file_id'], row['uploaded_at'], row['media']))

        else:
            async with db.execute("SELECT * FROM materials ORDER BY course_id, title") as cursor:
                async for row in cursor:
                    materials.append((row['id'], row['course_id'], row['title'], row['type'], row['telegram_file_id'], row['uploaded_at'], row['media']))

    return materials    


#=====================
async def remove_material(material_id: int):
    """Removes a material from the database"""
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute(
            "DELETE FROM materials WHERE id = ?", (material_id,)
        )
        await db.commit()
        if cursor.rowcount == 0:
            logger.warning(f"Attempted to remove material with ID: {material_id}, but it does not exist.")
            return False

        logger.info(f"Removed material with ID: {material_id}")
        return True


#=====================
async def add_resource(course_id: int, title: str, url: str):
    """Adds a new resource to the database and returns its ID"""
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute(
            """INSERT INTO resources (course_id, title, url)
            VALUES (?, ?, ?)""", (course_id, title, url)
        )
        await db.commit()
        logger.info(f"Added a new resource with: course_id={course_id}, title={title}, url={url}")
        return cursor.lastrowid


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
async def remove_resource(resource_id: int):
    """Removes a resource from the database"""
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute(
            "DELETE FROM resources WHERE id = ?", (resource_id,)
        )
        await db.commit()
        if cursor.rowcount == 0:
            logger.warning(f"Attempted to remove resource with ID: {resource_id}, but it does not exist.")
            return False

        logger.info(f"Removed resource with ID: {resource_id}")
        return True


#=====================
# Helpers used by the admin panel & contribution review
#=====================
async def _fetchone(query: str, params: tuple = ()):
    async with aiosqlite.connect("database.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            row = await cursor.fetchone()
    return dict(row) if row else None


async def _fetchall(query: str, params: tuple = ()):
    async with aiosqlite.connect("database.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def _execute(query: str, params: tuple = ()):
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute(query, params)
        await db.commit()
        return cursor


#=====================
async def get_course(course_id: int):
    """Gets a course row as a dict (or None)"""
    return await _fetchone("SELECT * FROM courses WHERE id = ?", (course_id,))


async def get_material(material_id: int):
    """Gets a material row as a dict (or None)"""
    return await _fetchone("SELECT * FROM materials WHERE id = ?", (material_id,))


async def get_resource(resource_id: int):
    """Gets a resource row as a dict (or None)"""
    return await _fetchone("SELECT * FROM resources WHERE id = ?", (resource_id,))


async def list_materials(course_id: int, material_type: str):
    """Materials of a course/type as dicts"""
    return await _fetchall(
        "SELECT * FROM materials WHERE course_id = ? AND type = ? ORDER BY title, id",
        (course_id, material_type)
    )


async def list_resources(course_id: int):
    """Resources of a course as dicts"""
    return await _fetchall("SELECT * FROM resources WHERE course_id = ? ORDER BY title, id", (course_id,))


async def count_materials_by_type(course_id: int):
    """Returns {type: count} for a course"""
    rows = await _fetchall(
        "SELECT type, COUNT(*) AS n FROM materials WHERE course_id = ? GROUP BY type", (course_id,)
    )
    return {row["type"]: row["n"] for row in rows}


async def get_stats():
    """Overall counts for the admin panel"""
    async with aiosqlite.connect("database.db") as db:
        stats = {}
        for key, query in (
            ("courses", "SELECT COUNT(*) FROM courses"),
            ("materials", "SELECT COUNT(*) FROM materials"),
            ("resources", "SELECT COUNT(*) FROM resources"),
            ("pending", "SELECT COUNT(*) FROM contributions WHERE status = 'pending'"),
        ):
            async with db.execute(query) as cursor:
                stats[key] = (await cursor.fetchone())[0]
    return stats


async def update_material(material_id: int, **fields):
    """Updates title/type/course_id of a material"""
    allowed = {k: v for k, v in fields.items() if k in ("title", "type", "course_id")}
    if not allowed:
        return False
    sets = ", ".join(f"{k} = ?" for k in allowed)
    cursor = await _execute(f"UPDATE materials SET {sets} WHERE id = ?", (*allowed.values(), material_id))
    logger.info(f"Updated material {material_id}: {allowed}")
    return cursor.rowcount > 0


async def update_resource(resource_id: int, **fields):
    """Updates title/url of a resource"""
    allowed = {k: v for k, v in fields.items() if k in ("title", "url")}
    if not allowed:
        return False
    sets = ", ".join(f"{k} = ?" for k in allowed)
    cursor = await _execute(f"UPDATE resources SET {sets} WHERE id = ?", (*allowed.values(), resource_id))
    logger.info(f"Updated resource {resource_id}: {allowed}")
    return cursor.rowcount > 0


async def remove_course_cascade(course_id: int):
    """Removes a course with all of its materials and resources.
    Returns (course_removed, materials_removed, resources_removed)"""
    async with aiosqlite.connect("database.db") as db:
        m = await db.execute("DELETE FROM materials WHERE course_id = ?", (course_id,))
        r = await db.execute("DELETE FROM resources WHERE course_id = ?", (course_id,))
        c = await db.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        await db.commit()
    logger.info(f"Removed course {course_id} with {m.rowcount} materials and {r.rowcount} resources")
    return c.rowcount > 0, m.rowcount, r.rowcount


#=====================
# Contributions
async def create_batch(user_id: int, user_label: str):
    cursor = await _execute(
        "INSERT INTO contribution_batches (user_id, user_label) VALUES (?, ?)", (user_id, user_label)
    )
    return cursor.lastrowid


async def get_batch(batch_id: int):
    return await _fetchone("SELECT * FROM contribution_batches WHERE id = ?", (batch_id,))


async def update_batch(batch_id: int, **fields):
    allowed = {k: v for k, v in fields.items() if k in ("description", "card_chat_id", "card_message_id")}
    sets = ", ".join(f"{k} = ?" for k in allowed)
    await _execute(f"UPDATE contribution_batches SET {sets} WHERE id = ?", (*allowed.values(), batch_id))


async def add_contribution(user_id: int, user_label: str, kind: str, batch_id: int = None,
                           file_id: str = None, media: str = None, file_name: str = None, urls: str = None):
    cursor = await _execute(
        """INSERT INTO contributions (batch_id, user_id, user_label, kind, file_id, media, file_name, urls)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (batch_id, user_id, user_label, kind, file_id, media, file_name, urls)
    )
    return cursor.lastrowid


async def get_contribution(contribution_id: int):
    return await _fetchone("SELECT * FROM contributions WHERE id = ?", (contribution_id,))


async def get_batch_contributions(batch_id: int, status: str = None):
    if status:
        return await _fetchall(
            "SELECT * FROM contributions WHERE batch_id = ? AND status = ? ORDER BY id", (batch_id, status)
        )
    return await _fetchall("SELECT * FROM contributions WHERE batch_id = ? ORDER BY id", (batch_id,))


async def set_contribution_card(contribution_id: int, chat_id: int, message_id: int):
    await _execute(
        "UPDATE contributions SET card_chat_id = ?, card_message_id = ? WHERE id = ?",
        (chat_id, message_id, contribution_id)
    )


async def set_contribution_status(contribution_id: int, status: str, reviewer_id: int):
    """Marks a pending contribution as reviewed. Returns False if it was already reviewed."""
    cursor = await _execute(
        """UPDATE contributions SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
        WHERE id = ? AND status = 'pending'""",
        (status, reviewer_id, contribution_id)
    )
    return cursor.rowcount > 0
