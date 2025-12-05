import datetime
from database.db import get_db

class WithdrawService:

    @staticmethod
    async def create_withdraw(user_id: int, amount_usdt: float, wallet: str, method: str):
        db = await get_db()
        now = datetime.datetime.utcnow().isoformat()

        cur = await db.execute(
            "INSERT INTO withdraws (user_id, amount_usdt, wallet, method, status, created_at) "
            "VALUES (?, ?, ?, ?, 'pending', ?)",
            (user_id, amount_usdt, wallet, method, now)
        )
        await db.commit()
        wd_id = cur.lastrowid
        await db.close()
        return wd_id

    @staticmethod
    async def get_withdraw(wd_id: int):
        db = await get_db()
        cursor = await db.execute("SELECT * FROM withdraws WHERE id = ?", (wd_id,))
        wd = await cursor.fetchone()
        await db.close()
        return wd

    @staticmethod
    async def get_by_status(status: str):
        db = await get_db()
        cursor = await db.execute(
            "SELECT * FROM withdraws WHERE status = ? ORDER BY created_at DESC",
            (status,)
        )
        rows = await cursor.fetchall()
        await db.close()
        return rows

    @staticmethod
    async def has_pending(user_id: int) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "SELECT id FROM withdraws WHERE user_id = ? AND status = 'pending' LIMIT 1",
            (user_id,)
        )
        row = await cursor.fetchone()
        await db.close()
        return bool(row)

    @staticmethod
    async def approve_withdraw(wd_id: int):
        db = await get_db()

        cursor = await db.execute("SELECT * FROM withdraws WHERE id = ?", (wd_id,))
        wd = await cursor.fetchone()

        if not wd:
            await db.close()
            return "not_found"

        if wd["status"] != "pending":
            await db.close()
            return "already_processed"

        user_id = wd["user_id"]
        amount = wd["amount_usdt"]


        cursor2 = await db.execute(
            "SELECT balance_usdt FROM users WHERE tg_id = ?", (user_id,)
        )
        user = await cursor2.fetchone()

        if user["balance_usdt"] < amount:
            await db.execute(
                "UPDATE withdraws SET status='declined', processed_at=? WHERE id=?",
                (datetime.datetime.utcnow().isoformat(), wd_id)
            )
            await db.commit()
            await db.close()
            return "insufficient"


        await db.execute(
            "UPDATE users SET balance_usdt = balance_usdt - ? WHERE tg_id = ?",
            (amount, user_id)
        )


        await db.execute(
            "UPDATE withdraws SET status='approved', processed_at=? WHERE id=?",
            (datetime.datetime.utcnow().isoformat(), wd_id)
        )

        await db.commit()
        await db.close()
        return "success"

    @staticmethod
    async def decline_withdraw(wd_id: int):
        db = await get_db()

        cursor = await db.execute("SELECT * FROM withdraws WHERE id = ?", (wd_id,))
        wd = await cursor.fetchone()

        if not wd:
            await db.close()
            return "not_found"

        if wd["status"] != "pending":
            await db.close()
            return "already_processed"

        await db.execute(
            "UPDATE withdraws SET status='declined', processed_at=? WHERE id=?",
            (datetime.datetime.utcnow().isoformat(), wd_id)
        )

        await db.commit()
        await db.close()
        return "success"
    @staticmethod
    async def notify_admins_about_withdraw(bot, wd_id: int, user_id: int, amount: float, method: str, wallet: str):

        from config import ADMINS
        from keyboards.admin_finance import withdraw_action_kb

        text = (
            "📤 <b>Новая заявка на вывод</b>\n"
            f"ID: <b>{wd_id}</b>\n"
            f"Пользователь: <code>{user_id}</code>\n"
            f"Сумма: <b>{amount} USDT</b>\n"
            f"Метод: <b>{method.upper()}</b>\n"
            f"Кошелёк: <code>{wallet}</code>"
        )

        for admin in ADMINS:
            try:
                await bot.send_message(
                    admin,
                    text,
                    reply_markup=withdraw_action_kb(wd_id)
                )
            except Exception as e:
                print(f"[ERROR] Не удалось отправить админу {admin}: {e}")
