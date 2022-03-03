import logging
from typing import Union

import configcatclient
from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message, CallbackQuery

from config import cat_keys
from utils.db_api import database

config = configcatclient.create_client(cat_keys.ADMINISTRATION)


class UserInBase(BoundFilter):
    key = 'user_in_base'
    required = True

    def __init__(self, user_in_base):
        self.user_in_base = user_in_base

    async def check(self, message: Union[CallbackQuery, Message]):
        if isinstance(message, Message):
            chat_id = message.chat.id
        else:
            chat_id = message.message.chat.id
        if chat_id < 0 and chat_id != int(config.get_value('notify_chat_id', 0)):  # if its group or channel - ignore
            logging.info(f'Ignore user {message.chat.id}')
            return False
        logging.info(f'Success user {message.chat.id}')
        user = await database.get_user(user_id=chat_id)
        if not user:
            await database.create_user(chat_id)
        return True
