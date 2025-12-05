from aiogram.fsm.state import StatesGroup, State

class PhoneState(StatesGroup):
    entering_phone = State()
