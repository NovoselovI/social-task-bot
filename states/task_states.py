from aiogram.fsm.state import State, StatesGroup


class CreateTaskState(StatesGroup):
    choosing_type = State()
    entering_url = State()
    entering_total_views = State()
    entering_title = State()

class AdminCreateTaskState(StatesGroup):
    choosing_type = State()
    entering_url = State()
    entering_total_views = State()
    entering_title = State()