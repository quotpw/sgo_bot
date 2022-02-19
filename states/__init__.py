from aiogram.dispatcher.filters.state import StatesGroup, State


class SetupAccount(StatesGroup):
    city = State()
    org_type = State()
    org_id = State()
    username = State()
    password = State()
