from handlers.restrictred import pretty_date
from services.referrals_service import ReferralsService
from services.staking_service import StakingService
from services.task_service import TasksService
from services.user_service import UserService
BASE_PERCENT = 0.25
REF_PERCENT = 0.01

async def build_user_profile_text(user: dict) -> str:
    refs_count = await ReferralsService.count_referrals(user["tg_id"])
    stake = await StakingService.get_user(user["tg_id"])

    stake_amount = stake["stake_amount"] or 0
    stake_earned = stake["stake_earned"] or 0
    referrer_tg = "—"
    if user["referrer_id"]:
        ref_user = await UserService.get_user_by_id(user["referrer_id"])
        referrer_tg = ref_user["tg_id"] if ref_user else "—"
    earnings = await TasksService.get_user_earnings(user["tg_id"])
    percent = BASE_PERCENT + refs_count * REF_PERCENT
    daily_income = stake_amount * percent / 100
    return (
        f"👤 <b>Пользователь</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 TG ID: <code>{user['tg_id']}</code>\n"
        f"👤 Username: @{user['username']}\n"
        f"📌 Имя: {user['first_name']}\n"
        f"👥 Его пригласил: <code>{referrer_tg}</code>\n"
        f"📱 Телефон: {user['phone'] or '❌ не привязан'}\n"
        f"📅 Регистрация: {pretty_date(user['reg_date'])} (UTC)\n"
        f"⏱ Последняя активность: {pretty_date(user['last_active'])} (UTC)\n"
        f"💰 Баланс SD: <b>{user['balance_sd']:.2f}</b>\n"
        f"💵 Баланс USDT: <b>{user['balance_usdt']:.2f}</b>\n"
        f"💸 Заработано на заданиях: <b>{earnings:.2f} SD</b>\n"
        f"👥 Рефералов: <b>{refs_count}</b>\n"
        f"🚫 Блокировка: {'Да' if user['is_banned'] else 'Нет'}\n"
        f"\n<b>📊 Стейкинг</b>\n"
        f"📦 В стейке: <b>{stake_amount} SD</b>\n"
        f"💰 Заработано: <b>{stake_earned:.2f} SD</b>\n"
        f"🕒 Доход / 24h: <b>{daily_income:.2f} SD</b>\n"
    )
