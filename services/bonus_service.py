import datetime
from database.db import get_db

class BonusService:

    @staticmethod
    async def can_claim_bonus(user_id: int) -> bool:
        db = await get_db()
        try:
            cur = await db.execute("SELECT last_daily_bonus FROM users WHERE tg_id = ?", (user_id,))
            row = await cur.fetchone()
        finally:
            await db.close()

        last = row["last_daily_bonus"]
        if not last:
            return True

        last_dt = datetime.datetime.fromisoformat(last)
        now = datetime.datetime.utcnow()

        return (now - last_dt).total_seconds() >= 86400

    @staticmethod
    async def give_bonus(user_id: int, amount: float):
        now = datetime.datetime.utcnow().isoformat()
        db = await get_db()

        await db.execute(
            "UPDATE users SET balance_sd = balance_sd + ?, last_daily_bonus=? WHERE tg_id = ?",
            (amount, now, user_id)
        )

        await db.commit()
        await db.close()
