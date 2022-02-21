import random

from aiogram import types
from aiogram.dispatcher.filters import Text

from loader import dp, bot

cat_set = 'kittykittykitty_by_fStikBot'


@dp.message_handler(Text(contains='мяу', ignore_case=True))
@dp.message_handler(Text(contains='кот', ignore_case=True))
@dp.message_handler(Text(contains='гав', ignore_case=True))
@dp.message_handler(Text(contains='кис', ignore_case=True))
async def myau_handler(message: types.Message):
    sticker = random.choice((await bot.get_sticker_set(cat_set)).stickers).file_id
    await message.reply_sticker(sticker)
