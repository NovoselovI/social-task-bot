import datetime
import sqlite3

from database.db import get_db


class PromoCodeService:

    @staticmethod
    async def create(code: str, reward_sd: int, max_uses: int):
        db = await get_db()
        try:
            await db.execute("""
                INSERT INTO promocodes (code, reward_sd, max_uses, used_count, created_at)
                VALUES (?, ?, ?, 0, datetime('now'))
            """, (code, reward_sd, max_uses))
            await db.commit()
            return {"status": "ok"}

        except sqlite3.IntegrityError:
            return {"status": "exists"}

        finally:
            await db.close()

    @staticmethod
    async def get_paginated(offset: int, limit: int = 5):
        db = await get_db()

        cur = await db.execute(
            "SELECT * FROM promocodes ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        rows = await cur.fetchall()

        cur = await db.execute("SELECT COUNT(*) FROM promocodes")
        total = (await cur.fetchone())[0]

        await db.close()
        return rows, total

    @staticmethod
    async def delete(promo_id: int):
        db = await get_db()
        await db.execute("DELETE FROM promocodes WHERE id = ?", (promo_id,))
        await db.commit()
        await db.close()

    @staticmethod
    async def activate(user_id: int, code: str):
        db = await get_db()


        cur = await db.execute("SELECT * FROM promocodes WHERE code = ?", (code,))
        promo = await cur.fetchone()

        if not promo:
            await db.close()
            return {"status": "not_found"}


        if promo["used_count"] >= promo["max_uses"]:
            await db.close()
            return {"status": "limit_reached"}


        cur = await db.execute(
            "SELECT 1 FROM promo_uses WHERE user_id = ? AND promo_id = ?",
            (user_id, promo["id"])
        )
        already_used = await cur.fetchone()

        if already_used:
            await db.close()
            return {"status": "already_used"}


        await db.execute(
            "UPDATE promocodes SET used_count = used_count + 1 WHERE id = ?",
            (promo["id"],)
        )


        await db.execute(
            "UPDATE users SET balance_sd = balance_sd + ? WHERE tg_id = ?",
            (promo["reward_sd"], user_id)
        )


        now = int(datetime.datetime.utcnow().timestamp())
        await db.execute(
            "INSERT INTO promo_uses (promo_id, user_id, used_at) VALUES (?, ?, ?)",
            (promo["id"], user_id, now)
        )

        await db.commit()
        await db.close()

        return {"status": "ok", "reward": promo["reward_sd"]}
