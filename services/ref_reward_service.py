from database.db import get_db

class RefRewardService:

    @staticmethod
    async def get_reward():
        db = await get_db()
        try:
            cur = await db.execute("SELECT value FROM settings WHERE key = 'ref_reward'")
            row = await cur.fetchone()
        finally:
            await db.close()

        return float(row["value"]) if row else 1.0

    @staticmethod
    async def set_reward(value: float):
        db = await get_db()
        try:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES ('ref_reward', ?)",
                (value,)
            )
            await db.commit()
        finally:
            await db.close()
