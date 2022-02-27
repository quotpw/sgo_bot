from aiogram import executor
import sentry_sdk
from loader import dp
import middlewares, filters, handlers

if __name__ == '__main__':
    sentry_sdk.init(
        "https://5196aa9de3e84edc9b5deebaaa53a465@o1154088.ingest.sentry.io/6233749",
        traces_sample_rate=1.0
    )
    executor.start_polling(dp)
