from loader import dp
from .user_in_base import UserInBase
from .user_with_account import UserWithAccount

if __name__ == "filters":
    dp.filters_factory.bind(UserInBase)
    dp.filters_factory.bind(UserWithAccount)
