from aiogram import types
from aiogram.dispatcher.filters import Text

from utils.db_api import database
from loader import dp
from utils.sgo_api import Sgo


@dp.message_handler(Text('Средние оценки', ignore_case=True), user_with_account=True)
async def start_with_account(message: types.Message):
    user = await database.get_user(user_id=message.chat.id)
    await message.answer("Ожидайте, подготоваливаю данные.")
    obj = await Sgo(await database.get_account(id=user['account_id']))
    text = "<b>Средние оценки по предметам:</b>\n"
    for predmet in await obj.information_letter_for_parents():
        text += f"\n<i>{predmet[0]}</i>: <code>{predmet[1].replace('&nbsp;', '⁉️')}</code>"
    await message.reply(text)
    await obj.close()
