import aiosqlite
import logging

DB_PATH = "kinobot.db"
logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Ma'lumotlar bazasini yaratish va jadvallarni sozlash."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                code       TEXT    UNIQUE NOT NULL,
                message_id INTEGER NOT NULL,
                title      TEXT    DEFAULT '',
                added_at   TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER UNIQUE NOT NULL,
                username      TEXT    DEFAULT '',
                request_count INTEGER DEFAULT 0,
                joined_at     TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ads (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                text       TEXT    NOT NULL,
                button_text  TEXT  DEFAULT '',
                button_url   TEXT  DEFAULT '',
                every_n    INTEGER DEFAULT 3,
                is_active  INTEGER DEFAULT 1,
                created_at TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    logger.info("Ma'lumotlar bazasi tayyor.")


# ─── MOVIES ───────────────────────────────────────────────────────────────────

async def add_movie(code: str, message_id: int, title: str = "") -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO movies (code, message_id, title) VALUES (?, ?, ?)",
                (code, message_id, title),
            )
            await db.commit()
        return True
    except aiosqlite.IntegrityError:
        return False


async def get_movie(code: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movies WHERE code = ?", (code,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def delete_movie(code: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM movies WHERE code = ?", (code,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def list_movies() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movies ORDER BY added_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def movie_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM movies") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


# ─── USERS ────────────────────────────────────────────────────────────────────

async def register_user(user_id: int, username: str = "") -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username) VALUES (?, ?)
            ON CONFLICT(user_id) DO NOTHING
            """,
            (user_id, username or ""),
        )
        await db.commit()


async def increment_request_count(user_id: int) -> int:
    """So'rovlar sonini 1 ga oshiradi va yangi qiymatni qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET request_count = request_count + 1 WHERE user_id = ?",
            (user_id,),
        )
        await db.commit()
        async with db.execute(
            "SELECT request_count FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 1


async def user_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_all_user_ids() -> list[int]:
    """Broadcast uchun barcha user_id larni olish."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]


# ─── ADS ──────────────────────────────────────────────────────────────────────

async def add_ad(text: str, button_text: str = "", button_url: str = "", every_n: int = 3) -> int:
    """Yangi reklama qo'shish. Yangi reklama id sini qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO ads (text, button_text, button_url, every_n) VALUES (?, ?, ?, ?)",
            (text, button_text, button_url, every_n),
        )
        await db.commit()
        return cursor.lastrowid


async def get_active_ad() -> dict | None:
    """Faol reklamalardan birini (eng oxirgi) qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM ads WHERE is_active = 1 ORDER BY id DESC LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_ad_by_id(ad_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM ads WHERE id = ?", (ad_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def list_ads() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM ads ORDER BY id DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def toggle_ad(ad_id: int, is_active: bool) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE ads SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, ad_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def delete_ad(ad_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM ads WHERE id = ?", (ad_id,))
        await db.commit()
        return cursor.rowcount > 0


async def update_ad_every_n(ad_id: int, every_n: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE ads SET every_n = ? WHERE id = ?", (every_n, ad_id)
        )
        await db.commit()
        return cursor.rowcount > 0
