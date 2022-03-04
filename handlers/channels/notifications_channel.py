import asyncio

import aiogram.utils.exceptions
import configcatclient
from aiogram import types

from config import cat_keys
from loader import dp, bot
from utils.db_api import database

config = configcatclient.create_client(cat_keys.ADMINISTRATION)

notify_chat_id = int(config.get_value('notify_chat_id', 0))


@dp.channel_post_handler(chat_id=notify_chat_id)
async def notifications_from_channel(message: types.Message):
    users = await database.get_users()
    sent = 0
    sent_error = 0
    for user in users:
        if user['user_id'] == notify_chat_id:
            continue
        try:
            await bot.forward_message(user['user_id'], message.chat.id, message.message_id, disable_notification=True)
            sent += 1
        except aiogram.utils.exceptions.BotBlocked:
            await database.delete_user(user['user_id'])
            sent_error += 1
        await asyncio.sleep(0.5)
    await message.answer(
        f'Messages sent to: <code>{sent}</code>!\n'
        f'Deleted users: <code>{sent_error}</code>'
    )
