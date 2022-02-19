from aiogram import types
from utils.db_api import database
from loader import dp, bot

menu_markup = types.ReplyKeyboardMarkup(
    [[types.KeyboardButton("Получить рассписание"), types.KeyboardButton("Средние оценки")]],
    resize_keyboard=True
)


@dp.message_handler(user_with_account=False, commands=['start'])
async def start_without_account(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.full_name}!\n"
        f"Чтоб бот заработал, надо пройти аунтефикацию в <code>sgo.rso23.ru</code>.\n"
        f"Нажми /auth для аунтефикации :)"
    )


@dp.message_handler(user_with_account=True, commands=['start'])
async def start_with_account(message: types.Message):
    user = await database.get_user(user_id=message.chat.id)
    account = await database.get_account(id=user['account_id'])
    await bot.send_message(message.chat.id, f"Привет, {account['name']}!", reply_markup=menu_markup)
