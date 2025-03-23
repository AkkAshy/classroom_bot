from aiohttp import web
import logging
import asyncio
from bot import main  # Импортируем функцию main из bot.py

logging.basicConfig(level=logging.INFO)

async def healthcheck(request):
    """Эндпоинт для проверки работоспособности."""
    return web.Response(text="Бот работает!")

app = web.Application()
app.add_routes([web.get("/", healthcheck)])

async def start_bot():
    """Функция для запуска бота в фоне."""
    asyncio.create_task(main())

if __name__ == "__main__":
    start_bot()
    web.run_app(app, port=10000)  # Render требует, чтобы приложение слушало порт
