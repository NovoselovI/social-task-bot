from database.db import get_db

class TechService:

    @staticmethod
    async def get_mode() -> bool:
        
        db = await get_db()
        cur = await db.execute(
            "SELECT value FROM settings WHERE key = 'maintenance_mode'"
        )
        row = await cur.fetchone()
        await db.close()

        if not row:
            return True

        return row["value"] == "on"

    @staticmethod
    async def set_mode(enabled: bool):

        value = "on" if enabled else "off"

        db = await get_db()
        await db.execute(
            """
            INSERT OR REPLACE INTO settings (key, value)
            VALUES ('maintenance_mode', ?)
            """,
            (value,)
        )
        await db.commit()
        await db.close()
