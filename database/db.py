import aiosqlite
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bot.db")

async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    await db.execute("PRAGMA journal_mode=WAL;")
    await db.execute("PRAGMA synchronous=NORMAL;")
    await db.execute("PRAGMA busy_timeout = 5000;")
    db.row_factory = aiosqlite.Row
    return db
