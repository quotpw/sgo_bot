from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import configcatclient

config = configcatclient.create_client('XvnZCMXRUk2AYlhFwpHeCg/0oW9esHgO0iliYuGz8jTcQ')

bot = Bot(
    config.get_value('token', "5159657063:AAHs6Jk3fqbpW35rM6ztBHxo2EpdRTJOnLE"),
    parse_mode=types.ParseMode.HTML
)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
