import datetime
from database.db import get_db

class UserService:

    @staticmethod
    async def get_user(tg_id: int):
        db = await get_db()
        cursor = await db.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        user = await cursor.fetchone()
        await db.close()
        return user

    @staticmethod
    async def create_user(tg_id: int, username: str | None, first_name: str | None, referrer_id: int | None = None):
        db = await get_db()
        try:
            reg_date = datetime.datetime.utcnow().isoformat()
            last_active = reg_date

            await db.execute(
                """
                INSERT OR IGNORE INTO users (
                    tg_id, username, first_name, referrer_id,
                    balance_sd, balance_usdt, phone,
                    reg_date, last_active, is_banned,
                    stake_amount, stake_last_claim, stake_earned
                ) VALUES (?, ?, ?, ?, 0, 0, NULL, ?, ?, 0, 0, NULL, 0)
                """,
                (
                    tg_id, username, first_name, referrer_id,
                    reg_date, last_active
                )
            )

            await db.commit()
        finally:
            await db.close()

    @staticmethod
    async def increment_balance_sd(user_id: int, amount: float):

        db = await get_db()
        try:
            await db.execute(
                "UPDATE users SET balance_sd = balance_sd + ? WHERE id = ?",
                (amount, user_id)
            )
            await db.commit()
        finally:
            await db.close()

    @staticmethod
    async def update_last_active(tg_id: int):
        db = await get_db()
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()

        try:
            await db.execute(
                "UPDATE users SET last_active = ? WHERE tg_id = ?",
                (now, tg_id)
            )
            await db.commit()
        finally:
            await db.close()

    @staticmethod
    async def get_user_by_username(username: str):
        db = await get_db()
        cursor = await db.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = await cursor.fetchone()
        await db.close()
        return user
    @staticmethod
    async def get_user_by_id(user_id: int):
        db = await get_db()
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        await db.close()
        return row
    @staticmethod
    async def ban_user(tg_id: int):
        db = await get_db()
        await db.execute(
            "UPDATE users SET is_banned = 1 WHERE tg_id = ?",
            (tg_id,)
        )
        await db.commit()
        await db.close()

    @staticmethod
    async def unban_user(tg_id: int):
        db = await get_db()
        try:
            await db.execute(
                "UPDATE users SET is_banned = 0 WHERE tg_id = ?",
                (tg_id,)
            )
            await db.commit()
        finally:
            await db.close()

    @staticmethod
    async def update_balance_sd(tg_id: int, new_balance: float):
        db = await get_db()
        try:
            await db.execute(
                "UPDATE users SET balance_sd = ? WHERE tg_id = ?",
                (new_balance, tg_id)
            )
            await db.commit()
        finally:
            await db.close()

    @staticmethod
    async def update_balance_usdt(tg_id: int, new_balance: float):
        db = await get_db()
        try:
            await db.execute(
                "UPDATE users SET balance_usdt = ? WHERE tg_id = ?",
                (new_balance, tg_id)
            )
            await db.commit()
        finally:
            await db.close()