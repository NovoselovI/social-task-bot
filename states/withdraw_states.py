from aiogram.fsm.state import StatesGroup, State

class WithdrawState(StatesGroup):
    choosing_method = State()
    entering_amount = State()
    entering_wallet = State()
