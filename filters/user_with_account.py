from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message
from utils.db_api import database


class UserWithAccount(BoundFilter):
    key = 'user_with_account'

    def __init__(self, user_with_account):
        self.user_with_account = user_with_account

    async def check(self, message: Message):
        user = await database.get_user(user_id=message.from_user.id)
        if user:
            return bool(user['account_id']) is self.user_with_account
        else:
            return False
