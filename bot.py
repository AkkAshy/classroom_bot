import logging
import os
import asyncio
from aiogram import Bot, Dispatcher
<<<<<<< HEAD
from handlers import start, cources, role, teacher, student
=======

from handlers import start, cources, role, teacher, student, test_creator
>>>>>>> 4a93b39 (Обновил файлы: исправил получение email через People API)
from server import start_server  # Импортируем сервер
import tracemalloc
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not os.path.exists("logs"):
    os.makedirs("logs")


logging.basicConfig(
    level=logging.DEBUG,  # Максимальный уровень логов
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),  # Запись в файл
        logging.StreamHandler()  # Вывод в консоль
    ]
)


logging.info("🚀 Логирование настроено! Все события пишутся в logs/bot.log")

tracemalloc.start()
logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(student.router)
dp.include_router(cources.router)
dp.include_router(role.router)
dp.include_router(teacher.router)
dp.include_router(test_creator.router)

async def main():
    """Запуск и бота, и сервера"""
    logging.info("🚀 Бот запускается...")
    await asyncio.sleep(2) # Небольшая задержка для старта
    await bot.delete_webhook(drop_pending_updates=True)

    # Запускаем aiohttp-сервер параллельно с ботом
    server_task = asyncio.create_task(start_server())
    bot_task = asyncio.create_task(dp.start_polling(bot))

    await asyncio.gather(server_task, bot_task)  # Оба процесса запускаются одновременно

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Бот остановлен вручную (Ctrl+C).")
