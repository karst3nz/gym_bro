import sys
from threading import Thread
from config import *
from database.db import DB
from handlers import msg, inline, cmd
from utils.log import create_logger
import asyncio
logger = create_logger(__name__)


async def start_bot():
    await bot.set_my_commands([
            types.BotCommand(command="/start", description="Главное меню"),
            types.BotCommand(command="/weight", description="Ввести текущий вес"),
            types.BotCommand(command="/workset", description="Добавить рабочий подход"),
            types.BotCommand(command="/record", description="Добавить рекорд"),
            types.BotCommand(command="/weight_stats", description="Посмотреть статистику по весу тела"),
            types.BotCommand(command="/workset_stats", description="Посмотреть статистику по рабочим подходам"),
        ])
    await dp.start_polling(bot, close_bot_session=False, handle_signals=False)


if __name__ == '__main__':
    db = DB()
    asyncio.run(start_bot(), debug=False)
