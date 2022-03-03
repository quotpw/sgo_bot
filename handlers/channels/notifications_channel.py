import asyncio

import aiogram.utils.exceptions
import configcatclient
from aiogram import types

from config import cat_keys
from loader import dp, bot
from utils.db_api import database

config = configcatclient.create_client(cat_keys.ADMINISTRATION)


@dp.channel_post_handler(chat_id=int(config.get_value('notify_chat_id', 0)))
async def notifications_from_channel(message: types.Message):
    users = await database.get_users()
    for user in users:
        try:
            await bot.forward_message(user['user_id'], message.chat.id, message.message_id)
        except aiogram.utils.exceptions.BotBlocked:
            await database.delete_user(user['user_id'])
        await asyncio.sleep(0.5)
