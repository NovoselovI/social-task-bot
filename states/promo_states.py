from aiogram.fsm.state import State, StatesGroup

class PromoCreateState(StatesGroup):
    waiting_for_code = State()
    waiting_for_reward = State()
    waiting_for_limit = State()

class PromoState(StatesGroup):
    entering = State()