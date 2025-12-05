import datetime
from database.db import get_db

class StakingService:

    @staticmethod
    async def get_user(user_id: int):
        db = await get_db()
        cur = await db.execute(
            "SELECT stake_amount, stake_last_claim, stake_earned FROM users WHERE tg_id = ?",
            (user_id,)
        )
        row = await cur.fetchone()
        await db.close()
        return row

    @staticmethod
    async def get_referrals_count(user_id: int):
        db = await get_db()
        cur = await db.execute(
            "SELECT COUNT(*) as cnt FROM referrals WHERE ref_id = ?",
            (user_id,)
        )
        row = await cur.fetchone()
        await db.close()
        return row["cnt"]

    @staticmethod
    async def update_stake(user_id: int, amount: float):
        db = await get_db()

        await db.execute(
            "UPDATE users SET "
            "balance_sd = balance_sd - ?, "
            "stake_amount = stake_amount + ?, "
            "stake_last_claim = ? "
            "WHERE tg_id = ?",
            (amount, amount, datetime.datetime.utcnow().isoformat(), user_id)
        )

        await db.commit()
        await db.close()

    @staticmethod
    async def withdraw_stake(user_id: int):
        db = await get_db()
        cur = await db.execute(
            "SELECT stake_amount FROM users WHERE tg_id = ?", (user_id,)
        )
        row = await cur.fetchone()
        amount = row["stake_amount"]

        await db.execute(
            "UPDATE users SET stake_amount = 0, balance_sd = balance_sd + ?, stake_last_claim = NULL",
            (amount,)
        )
        await db.commit()
        await db.close()
        return amount

    @staticmethod
    async def update_claim(user_id: int, reward: float):
        db = await get_db()
        await db.execute(
            "UPDATE users SET balance_sd = balance_sd + ?, stake_earned = stake_earned + ?, stake_last_claim = ? WHERE tg_id = ?",
            (reward, reward, datetime.datetime.utcnow().isoformat(), user_id)
        )
        await db.commit()
        await db.close()
