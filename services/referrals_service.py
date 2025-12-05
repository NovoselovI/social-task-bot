import datetime
from database.db import get_db
from services.ref_reward_service import RefRewardService
from services.user_service import UserService
from config import REF_PERCENT_LEVEL_1, REF_PERCENT_LEVEL_2,BOT_TOKEN

class ReferralsService:


    @staticmethod
    async def get_referrals(referrer_tg_id: int):
        db = await get_db()
        try:
            cursor = await db.execute(
                """
                SELECT 
                    u.tg_id,
                    u.username,
                    u.first_name
                FROM referrals r
                JOIN users u ON u.tg_id = r.user_id
                WHERE r.ref_id = ?
                ORDER BY r.id DESC
                """,
                (referrer_tg_id,)
            )
            rows = await cursor.fetchall()
        finally:
            await db.close()
        return rows

    @staticmethod
    async def count_referrals(referrer_tg_id: int):
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM referrals WHERE ref_id = ?",
                (referrer_tg_id,)
            )
            cnt = await cursor.fetchone()
        finally:
            await db.close()
        return cnt[0]

    @staticmethod
    async def attach_referral(invited_tg: int, inviter_tg: int):


        if invited_tg == inviter_tg:
            return

        db = await get_db()
        inviter_balance_row = None

        try:

            cur = await db.execute(
                "SELECT id, referrer_id FROM users WHERE tg_id = ?",
                (invited_tg,)
            )
            invited = await cur.fetchone()


            cur = await db.execute(
                "SELECT id, referrer_id FROM users WHERE tg_id = ?",
                (inviter_tg,)
            )
            inviter = await cur.fetchone()



            if not invited or not inviter:
                return


            if invited["referrer_id"]:
                print("🟥 ALREADY HAS REFERRER, STOP")
                return


            await db.execute(
                "UPDATE users SET referrer_id = ? WHERE id = ?",
                (inviter["id"], invited["id"])
            )


            now = datetime.datetime.utcnow().isoformat()

            await db.execute(
                """
                INSERT INTO referrals (user_id, ref_id, level, created_at)
                VALUES (?, ?, 1, ?)
                """,
                (invited_tg, inviter_tg, now)
            )



            second_level_id = inviter["referrer_id"]

            if second_level_id:
                cur2 = await db.execute(
                    "SELECT tg_id FROM users WHERE id = ?",
                    (second_level_id,)
                )
                second = await cur2.fetchone()


                if second:
                    await db.execute(
                        """
                        INSERT INTO referrals (user_id, ref_id, level, created_at)
                        VALUES (?, ?, 2, ?)
                        """,
                        (invited_tg, second["tg_id"], now)
                    )





            reward = await RefRewardService.get_reward()

            cur_bal = await db.execute(
                "SELECT balance_sd FROM users WHERE tg_id = ?",
                (inviter_tg,)
            )
            inviter_balance_row = await cur_bal.fetchone()

            if inviter_balance_row:
                new_balance = inviter_balance_row["balance_sd"] + reward

                await db.execute(
                    "UPDATE users SET balance_sd = ? WHERE tg_id = ?",
                    (new_balance, inviter_tg)
                )

                cur = await db.execute(
                    "SELECT balance_sd FROM users WHERE tg_id = ?",
                    (inviter_tg,)
                )
                row = await cur.fetchone()



            await db.commit()

        finally:

            await db.close()


        if inviter_balance_row:
            try:
                print("🟩 TRY SEND NOTIFICATION…")
                from aiogram import Bot
                bot = Bot(token=BOT_TOKEN)
                await bot.send_message(
                    inviter_tg,
                    f"🎉 У вас новый реферал!\n"
                    f"💰 Начислено: <b>{reward} SD</b>",parse_mode = "HTML"
                )
                await bot.session.close()
            except Exception as e:
                print("Ошибка уведомления реферала:", e)

