from aiogram import Router, types
from aiogram.filters import CommandStart



from utils.permissions import allow_without_subscription
from services.user_service import UserService
from services.referrals_service import ReferralsService
from keyboards.main_menu import main_menu

router = Router()


@allow_without_subscription
@router.message(CommandStart())
async def start_cmd(message: types.Message):
    tg_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name


    ref_id = None
    parts = message.text.split()
    if len(parts) > 1:
        try:
            ref_id = int(parts[1])
        except ValueError:
            ref_id = None


    if ref_id == tg_id:
        ref_id = None


    user = await UserService.get_user(tg_id)


    if not user:

        await UserService.create_user(
            tg_id=tg_id,
            username=username,
            first_name=first_name,
            referrer_id=None,
        )
        print("USER CREATED")


        if ref_id:
            await ReferralsService.attach_referral(
                invited_tg=tg_id,
                inviter_tg=ref_id
            )
    else:

        ref_id = None

    await message.answer(
        "🏦 Добро пожаловать в SMART DOLLAR\n📲 Платформа для зароботка реальных денег за выполнения заданий, просмотр рекламы, бонусы, стейкинг, лотерея, так же прокачивай свои ресурси, добавляя свои задание!",
        reply_markup=main_menu,parse_mode="HTML"
    )
