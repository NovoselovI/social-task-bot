from aiogram.fsm.state import State, StatesGroup

class ConvertSD(StatesGroup):
    waiting_for_amount = State()

class ConvertUSDT(StatesGroup):
    waiting_for_amount = State()
