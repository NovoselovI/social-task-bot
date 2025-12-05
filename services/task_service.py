import datetime
from database.db import get_db
from config import TASK_PRICE_FOR_OWNER, TASK_REWARD_FOR_WORKER,REF_PERCENT_LEVEL_1,REF_PERCENT_LEVEL_2


class TasksService:

    @staticmethod
    async def get_active_tasks():
        db = await get_db()
        cursor = await db.execute("SELECT * FROM tasks WHERE is_active = 1")
        tasks = await cursor.fetchall()
        await db.close()
        return tasks


    @staticmethod
    async def create_task_with_payment(
        tg_id: int,
        title: str,
        url: str,
        task_type: str,
        total_views: int,
        description: str | None = None,
    ):

        db = await get_db()


        cur = await db.execute(
            "SELECT id, balance_sd FROM users WHERE tg_id = ?",
            (tg_id,)
        )
        user = await cur.fetchone()

        if not user:
            await db.close()
            return {"status": "user_not_found"}


        cost = total_views * TASK_PRICE_FOR_OWNER
        if user["balance_sd"] < cost:
            await db.close()
            return {
                "status": "insufficient_funds",
                "need": cost,
                "balance": user["balance_sd"],
            }

        new_balance = user["balance_sd"] - cost
        now_ts = int(datetime.datetime.utcnow().timestamp())

        cur = await db.execute(
            """
            INSERT INTO tasks (
                title, description, reward_sd, type, is_active, is_admin_task,
                url, total_views, completed_views,
                owner_id, fee_percent, created_at, status
            )
            VALUES (?, ?, ?, ?, 1, 0, ?, ?, 0, ?, 0, ?, 'active')
            """,
            (
                title,
                description or "",
                TASK_REWARD_FOR_WORKER,
                task_type,
                url,
                total_views,
                user["id"],
                now_ts,
            )
        )

        task_id = cur.lastrowid


        await db.execute(
            "UPDATE users SET balance_sd = ? WHERE tg_id = ?",
            (new_balance, tg_id)
        )

        await db.commit()
        await db.close()

        return {
            "status": "ok",
            "task_id": task_id,
            "cost": cost,
            "new_balance": new_balance,
        }


    @staticmethod
    async def get_tasks_by_owner(owner_tg_id: int):
        db = await get_db()
        cur = await db.execute(
            """
            SELECT t.*
            FROM tasks t
            JOIN users u ON t.owner_id = u.id
            WHERE u.tg_id = ?
            ORDER BY t.created_at DESC
            """,
            (owner_tg_id,)
        )
        rows = await cur.fetchall()
        await db.close()
        return rows


    @staticmethod
    async def get_task_by_id(task_id: int):
        db = await get_db()
        cur = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = await cur.fetchone()
        await db.close()
        return task


    @staticmethod
    async def get_available_tasks_for_user(user_tg_id: int, limit: int = 20):

        db = await get_db()


        cur = await db.execute("SELECT id FROM users WHERE tg_id = ?", (user_tg_id,))
        user = await cur.fetchone()
        if not user:
            await db.close()
            return []

        user_id = user["id"]

        cur = await db.execute(
            """
            SELECT t.*
            FROM tasks t
            WHERE 
                t.is_active = 1
                AND t.status = 'active'
                AND (t.owner_id IS NULL OR t.owner_id != ?)
                AND t.total_views > t.completed_views
                AND t.id NOT IN (
                    SELECT task_id FROM user_tasks WHERE user_id = ?
                )
            ORDER BY t.is_admin_task DESC, t.created_at DESC
            LIMIT ?
            """,
            (user_id, user_id, limit)
        )

        tasks = await cur.fetchall()
        await db.close()
        return tasks
    @staticmethod
    async def get_available_tasks_chunk(user_tg_id: int, offset: int, limit: int = 15):
        db = await get_db()

        cur = await db.execute("SELECT id FROM users WHERE tg_id = ?", (user_tg_id,))
        user = await cur.fetchone()
        if not user:
            await db.close()
            return []

        user_id = user["id"]

        cur = await db.execute(
            """
            SELECT t.*
            FROM tasks t
            WHERE 
                t.is_active = 1
                AND t.status = 'active'
                AND (t.owner_id IS NULL OR t.owner_id != ?)
                AND t.total_views > t.completed_views
                AND t.id NOT IN (
                    SELECT task_id FROM user_tasks WHERE user_id = ?
                )
            ORDER BY t.is_admin_task DESC, t.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, user_id, limit, offset)
        )

        rows = await cur.fetchall()
        await db.close()
        return rows


    @staticmethod
    async def count_available_tasks(user_tg_id: int):
        db = await get_db()

        cur = await db.execute("SELECT id FROM users WHERE tg_id = ?", (user_tg_id,))
        user = await cur.fetchone()
        if not user:
            await db.close()
            return 0

        user_id = user["id"]

        cur = await db.execute(
            """
            SELECT COUNT(*)
            FROM tasks t
            WHERE 
                t.is_active = 1
                AND t.status = 'active'
                AND (t.owner_id IS NULL OR t.owner_id != ?)
                AND t.total_views > t.completed_views
                AND t.id NOT IN (
                    SELECT task_id FROM user_tasks WHERE user_id = ?
                )
            """,
            (user_id, user_id)
        )

        count = (await cur.fetchone())[0]
        await db.close()
        return count

    @staticmethod
    async def get_tasks_by_status(owner_tg_id: int, status: str):
        db = await get_db()
        cur = await db.execute(
            """
            SELECT t.*
            FROM tasks t
            JOIN users u ON t.owner_id = u.id
            WHERE u.tg_id = ? AND t.status = ?
            ORDER BY t.created_at DESC
            """,
            (owner_tg_id, status)
        )
        rows = await cur.fetchall()
        await db.close()
        return rows

    @staticmethod
    async def cancel_task(task_id: int, owner_tg_id: int):
        db = await get_db()


        cur = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = await cur.fetchone()
        if not task:
            await db.close()
            return {"status": "not_found"}


        cur = await db.execute("SELECT id, balance_sd FROM users WHERE tg_id = ?", (owner_tg_id,))
        user = await cur.fetchone()
        if not user or user["id"] != task["owner_id"]:
            await db.close()
            return {"status": "not_owner"}


        if task["status"] != "active":
            await db.close()
            return {"status": "not_active"}


        views_left = task["total_views"] - task["completed_views"]
        refund_total = views_left * TASK_PRICE_FOR_OWNER
        refund = refund_total * 0.75

        new_balance = user["balance_sd"] + refund


        await db.execute(
            "UPDATE users SET balance_sd = ? WHERE id = ?",
            (new_balance, user["id"])
        )


        await db.execute(
            "UPDATE tasks SET status = 'cancelled', is_active = 0 WHERE id = ?",
            (task_id,)
        )

        await db.commit()
        await db.close()

        return {"status": "ok", "refund": refund}

    @staticmethod
    async def get_my_tasks_by_status_paginated(owner_tg_id: int, status: str, offset: int, limit: int = 5):
        db = await get_db()

        cur = await db.execute("""
            SELECT u.id FROM users u WHERE u.tg_id = ?
        """, (owner_tg_id,))
        user = await cur.fetchone()
        if not user:
            await db.close()
            return [], 0

        user_id = user["id"]


        cur = await db.execute("""
            SELECT COUNT(*) FROM tasks
            WHERE owner_id = ? AND status = ?
        """, (user_id, status))

        total = (await cur.fetchone())[0]


        cur = await db.execute("""
            SELECT * FROM tasks
            WHERE owner_id = ? AND status = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (user_id, status, limit, offset))

        rows = await cur.fetchall()
        await db.close()
        return rows, total

    @staticmethod
    async def get_user_earnings(tg_id: int):
        db = await get_db()


        cur = await db.execute("SELECT id FROM users WHERE tg_id = ?", (tg_id,))
        row = await cur.fetchone()
        if not row:
            await db.close()
            return 0

        user_id = row["id"]


        cur = await db.execute(
            """
            SELECT COUNT(*) as cnt
            FROM user_tasks
            WHERE user_id = ?
            AND status = 'completed'
            """,
            (user_id,)
        )
        row = await cur.fetchone()
        await db.close()

        completed = row["cnt"]

        from config import TASK_REWARD_FOR_WORKER
        return completed * TASK_REWARD_FOR_WORKER

    @staticmethod
    async def admin_cancel_task(task_id: int, refund: bool):
        db = await get_db()

        cur = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = await cur.fetchone()

        if not task:
            await db.close()
            return {"status": "not_found"}

        owner_id = task["owner_id"]
        cur = await db.execute("SELECT * FROM users WHERE id = ?", (owner_id,))
        user = await cur.fetchone()

        views_left = task["total_views"] - task["completed_views"]
        cost_left = views_left * TASK_PRICE_FOR_OWNER

        refund_amount = cost_left * 0.75 if refund else 0

        if refund_amount > 0:
            new_balance = user["balance_sd"] + refund_amount
            await db.execute(
                "UPDATE users SET balance_sd = ? WHERE id = ?",
                (new_balance, owner_id)
            )

        await db.execute(
            "UPDATE tasks SET is_active = 0, status = 'cancelled' WHERE id = ?",
            (task_id,)
        )

        await db.commit()
        await db.close()

        return {"status": "ok", "user_tg_id": user["tg_id"]}

    @staticmethod
    async def get_active_tasks_admin(offset: int, limit: int):
        db = await get_db()
        cur = await db.execute(
            """
            SELECT *
            FROM tasks
            WHERE status='active' AND is_active=1
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )
        rows = await cur.fetchall()
        await db.close()
        return rows

    @staticmethod
    async def count_active_tasks_admin():
        db = await get_db()
        cur = await db.execute(
            "SELECT COUNT(*) FROM tasks WHERE status='active' AND is_active=1"
        )
        count = (await cur.fetchone())[0]
        await db.close()
        return count

    @staticmethod
    async def get_user_by_id(user_id: int):

        db = await get_db()
        cur = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = await cur.fetchone()
        await db.close()
        return user

    @staticmethod
    async def finish_task(task_id: int, user_tg: int):
        db = await get_db()
        try:

            cur = await db.execute(
                "SELECT id, balance_sd FROM users WHERE tg_id = ?",
                (user_tg,)
            )
            user = await cur.fetchone()
            if not user:
                return {"status": "no_user"}

            user_id = user["id"]
            user_balance = user["balance_sd"]


            cur = await db.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,)
            )
            task = await cur.fetchone()
            if not task:
                return {"status": "no_task"}


            if (
                    task["completed_views"] >= task["total_views"]
                    or task["status"] != "active"
                    or not task["is_active"]
            ):
                return {"status": "limits_reached"}


            cur = await db.execute(
                "SELECT * FROM user_tasks WHERE user_id = ? AND task_id = ? AND status='completed'",
                (user_id, task_id)
            )
            already = await cur.fetchone()
            if already:
                return {"status": "already_completed"}


            cur = await db.execute(
                "SELECT * FROM user_tasks WHERE user_id = ? AND task_id = ? AND status='started'",
                (user_id, task_id)
            )
            ut = await cur.fetchone()

            now = int(__import__("time").time())

            if not ut:

                cur = await db.execute(
                    "INSERT INTO user_tasks (user_id, task_id, status, started_at) "
                    "VALUES (?, ?, 'started', ?)",
                    (user_id, task_id, now)
                )
                ut_id = cur.lastrowid
            else:
                ut_id = ut["id"]

            reward = task["reward_sd"]


            await db.execute(
                "UPDATE user_tasks "
                "SET status='completed', completed_at=?, "
                "    viewed_at=COALESCE(viewed_at, started_at) "
                "WHERE id=?",
                (now, ut_id)
            )


            await db.execute(
                "UPDATE tasks SET completed_views = completed_views + 1 WHERE id = ?",
                (task_id,)
            )


            new_balance = user_balance + reward
            await db.execute(
                "UPDATE users SET balance_sd = ? WHERE id = ?",
                (new_balance, user_id)
            )

            #
            cur = await db.execute(
                "SELECT referrer_id FROM users WHERE id = ?",
                (user_id,)
            )
            row = await cur.fetchone()
            l1_id = row["referrer_id"] if row else None

            if l1_id:

                cur = await db.execute(
                    "SELECT balance_sd, referrer_id FROM users WHERE id = ?",
                    (l1_id,)
                )
                l1 = await cur.fetchone()
                if l1:
                    l1_reward = reward * REF_PERCENT_LEVEL_1
                    await db.execute(
                        "UPDATE users SET balance_sd = balance_sd + ? WHERE id = ?",
                        (l1_reward, l1_id)
                    )


                    l2_id = l1["referrer_id"]
                    if l2_id:
                        cur = await db.execute(
                            "SELECT balance_sd FROM users WHERE id = ?",
                            (l2_id,)
                        )
                        l2 = await cur.fetchone()
                        if l2:
                            l2_reward = reward * REF_PERCENT_LEVEL_2
                            await db.execute(
                                "UPDATE users SET balance_sd = balance_sd + ? WHERE id = ?",
                                (l2_reward, l2_id)
                            )


            if task["completed_views"] + 1 >= task["total_views"]:
                await db.execute(
                    "UPDATE tasks SET is_active=0, status='finished' WHERE id=?",
                    (task_id,)
                )

            await db.commit()
            return {"status": "ok", "reward": reward}

        finally:
            await db.close()

    @staticmethod
    async def create_admin_task(
        title: str,
        url: str,
        task_type: str,
        total_views: int,
        description: str | None = None,
    ):

        db = await get_db()
        now_ts = int(datetime.datetime.utcnow().timestamp())
        try:
            cur = await db.execute(
                """
                INSERT INTO tasks (
                    title, description, reward_sd, type, is_active, is_admin_task,
                    url, total_views, completed_views,
                    owner_id, fee_percent, created_at, status
                )
                VALUES (?, ?, ?, ?, 1, 1, ?, ?, 0, NULL, 0, ?, 'active')
                """,
                (
                    title,
                    description or "",
                    TASK_REWARD_FOR_WORKER,
                    task_type,
                    url,
                    total_views,
                    now_ts,
                )
            )

            task_id = cur.lastrowid
            await db.commit()
        finally:
            await db.close()

        return {"status": "ok", "task_id": task_id}

