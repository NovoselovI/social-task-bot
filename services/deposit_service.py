import datetime
from database.db import get_db


class DepositService:

    @staticmethod
    async def create_deposit(user_id: int, amount: float, method: str) -> int:

        db = await get_db()
        now = datetime.datetime.utcnow().isoformat()

        cur = await db.execute(
            "INSERT INTO deposits (user_id, amount_usdt, method, status, created_at) "
            "VALUES (?, ?, ?, 'pending', ?)",
            (user_id, amount, method, now)
        )
        await db.commit()

        dep_id = cur.lastrowid
        await db.close()
        return dep_id

    @staticmethod
    async def notify_admins_about_deposit(bot, dep_id: int, user_id: int, amount: float, method: str):
        from config import ADMINS, UAH_TO_USDT_RATE
        from keyboards.admin_finance import deposit_action_kb


        if method == "uah":
            amount_text = f"{amount} UAH"
        else:
            amount_text = f"{amount} USDT"

        text = (
            "🔔 <b>Новая заявка на пополнение</b>\n"
            f"ID заявки: <b>{dep_id}</b>\n"
            f"Пользователь: <code>{user_id}</code>\n"
            f"Сумма: <b>{amount_text}</b>\n"
            f"Метод: <b>{method.upper()}</b>"
        )

        for admin in ADMINS:
            try:
                await bot.send_message(
                    admin,
                    text,
                    reply_markup=deposit_action_kb(dep_id)
                )
            except Exception as e:
                print(f"[ERROR] Не удалось отправить админу {admin}: {e}")



    @staticmethod
    async def get_by_status(status: str):

        db = await get_db()
        cursor = await db.execute(
            "SELECT * FROM deposits WHERE status = ? ORDER BY created_at DESC",
            (status,)
        )
        rows = await cursor.fetchall()
        await db.close()
        return rows

    @staticmethod
    async def get_deposit(dep_id: int):

        db = await get_db()
        cursor = await db.execute("SELECT * FROM deposits WHERE id = ?", (dep_id,))
        row = await cursor.fetchone()
        await db.close()
        return row



    @staticmethod
    async def get_pending_deposits():
        db = await get_db()
        cursor = await db.execute(
            "SELECT * FROM deposits WHERE status = 'pending' ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        await db.close()
        return rows

    @staticmethod
    async def approve_deposit(dep_id: int):
        db = await get_db()

        cursor = await db.execute("SELECT * FROM deposits WHERE id = ?", (dep_id,))
        dep = await cursor.fetchone()

        if not dep:
            await db.close()
            return "not_found"


        if dep["status"] != "pending":
            await db.close()
            return "already_processed"

        user_id = dep["user_id"]
        amount = dep["amount_usdt"]
        method = dep["method"]


        if method in ("ton", "bep20"):
            await db.execute(
                "UPDATE users SET balance_usdt = balance_usdt + ? WHERE tg_id = ?",
                (amount, user_id)
            )



        elif method == "uah":

            from config import UAH_TO_USDT_RATE



            usdt = amount / UAH_TO_USDT_RATE

            await db.execute(

                "UPDATE users SET balance_usdt = balance_usdt + ? WHERE tg_id = ?",

                (usdt, user_id)

            )

        await db.execute(
            "UPDATE deposits SET status='approved' WHERE id = ?",
            (dep_id,)
        )

        await db.commit()
        await db.close()
        return "success"

    @staticmethod
    async def decline_deposit(dep_id: int):
        db = await get_db()

        cursor = await db.execute("SELECT * FROM deposits WHERE id = ?", (dep_id,))
        dep = await cursor.fetchone()

        if not dep:
            await db.close()
            return "not_found"

        if dep["status"] != "pending":
            await db.close()
            return "already_processed"

        await db.execute(
            "UPDATE deposits SET status='declined' WHERE id = ?",
            (dep_id,)
        )

        await db.commit()
        await db.close()
        return "success"

    @staticmethod
    async def count_recent(user_id: int, minutes: int = 10) -> int:
        import datetime
        db = await get_db()

        time_limit = (datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)).isoformat()

        cursor = await db.execute(
            """
            SELECT COUNT(*) as cnt
            FROM deposits
            WHERE user_id = ?
              AND created_at >= ?
            """,
            (user_id, time_limit)
        )
        row = await cursor.fetchone()
        await db.close()
        return row["cnt"]

    @staticmethod
    async def set_setting(key, value):
        db = await get_db()
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        await db.commit()
        await db.close()

    @staticmethod
    async def get_setting(key):
        db = await get_db()
        cur = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cur.fetchone()
        await db.close()
        return row["value"] if row else None
