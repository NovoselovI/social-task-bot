import time
from database.db import get_db
from services.referrals_service import ReferralsService
from services.user_service import UserService


MINERS_CONFIG = {
    1: {"price": 100.0, "min_refs": 5, "per_day": 1.0},   # 1 SD / 24ч
    2: {"price": 500.0, "min_refs": 10, "per_day": 5.0},  # 5 SD / 24ч
}


class MinerService:
    @staticmethod
    async def get_user_miners(tg_id: int):

        user = await UserService.get_user(tg_id)
        if not user:
            return []
        user_id = user["id"]

        db = await get_db()
        try:
            cur = await db.execute("SELECT * FROM miners WHERE user_id = ?", (user_id,))
            rows = await cur.fetchall()
        finally:
            await db.close()
        return rows

    @staticmethod
    async def buy_miner(tg_id: int, miner_type: int):

        cfg = MINERS_CONFIG.get(miner_type)
        if not cfg:
            return {"status": "invalid_type"}

        user = await UserService.get_user(tg_id)
        if not user:
            return {"status": "no_user"}


        refs = await ReferralsService.count_referrals(tg_id)
        if refs < cfg["min_refs"]:
            return {
                "status": "not_enough_refs",
                "need": cfg["min_refs"],
                "have": refs,
            }

        balance = user["balance_sd"] or 0
        if balance < cfg["price"]:
            return {
                "status": "not_enough_balance",
                "price": cfg["price"],
                "balance": balance,
            }

        db = await get_db()
        user_id = user["id"]

        # уже куплен?
        cur = await db.execute(
            "SELECT id FROM miners WHERE user_id = ? AND miner_type = ?",
            (user_id, miner_type)
        )
        existing = await cur.fetchone()
        if existing:
            await db.close()
            return {"status": "already_bought"}

        now = int(time.time())

        await db.execute(
            "INSERT INTO miners (user_id, miner_type, bought_at, last_claim_at) VALUES (?, ?, ?, ?)",
            (user_id, miner_type, now, now)
        )

        await db.execute(
            "UPDATE users SET balance_sd = balance_sd - ? WHERE id = ?",
            (cfg["price"], user_id)
        )

        await db.commit()
        await db.close()

        return {
            "status": "ok",
            "price": cfg["price"],
        }

    @staticmethod
    async def claim_income(tg_id: int):


        user = await UserService.get_user(tg_id)
        if not user:
            return {"status": "no_user"}

        user_id = user["id"]
        db = await get_db()
        cur = await db.execute("SELECT * FROM miners WHERE user_id = ?", (user_id,))
        miners = await cur.fetchall()

        if not miners:
            await db.close()
            return {"status": "no_miners"}

        now = int(time.time())
        total_income = 0.0

        for m in miners:
            cfg = MINERS_CONFIG.get(m["miner_type"])
            if not cfg:
                continue

            last = m["last_claim_at"] or m["bought_at"]
            elapsed = max(0, now - last)
            if elapsed <= 0:
                continue

            per_sec = cfg["per_day"] / 86400.0
            inc = elapsed * per_sec

            total_income += inc

            await db.execute(
                "UPDATE miners SET last_claim_at = ? WHERE id = ?",
                (now, m["id"])
            )

        if total_income <= 0:
            await db.close()
            return {"status": "nothing_to_claim"}

        await db.execute(
            "UPDATE users SET balance_sd = balance_sd + ? WHERE id = ?",
            (total_income, user_id)
        )

        await db.commit()
        await db.close()

        return {
            "status": "ok",
            "amount": total_income,
        }
