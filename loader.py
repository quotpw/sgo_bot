import configcatclient
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import cat_keys

config = configcatclient.create_client(cat_keys.TELEGRAM)

bot = Bot(
    config.get_value('token', "5159657063:AAHs6Jk3fqbpW35rM6ztBHxo2EpdRTJOnLE"),
    parse_mode=types.ParseMode.HTML
)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
