from aiogram.fsm.state import State, StatesGroup


class LinkState(StatesGroup):
    waiting_code = State()


class AttendanceState(StatesGroup):
    group = State()
    date = State()
    lesson_id = State()
    topic = State()
    marking = State()