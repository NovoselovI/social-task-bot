from aiogram.fsm.state import State, StatesGroup

class BroadcastStates(StatesGroup):
    text = State()           # массовая текстовая
    photo = State()          # массовая фото
    personal_id = State()    # личная рассылка: ввод ID
    personal_text = State()  # личная рассылка: ввод текста
