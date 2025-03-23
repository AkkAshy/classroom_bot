import logging
import aiohttp.web as web
from services.google_auth import handle_auth_request, handle_oauth_callback

app = web.Application()
app.router.add_get("/auth", handle_auth_request)  # Запрос на авторизацию
app.router.add_get("/oauth_callback", handle_oauth_callback)  # Callback

async def start_server():
    """Функция запуска сервера"""
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)  # Сервер слушает порт 8080
    await site.start()
    logging.info("🌍 AIOHTTP сервер запущен на http://localhost:8080")

if __name__ == "__main__":
    logging.info("🚀 Запуск сервера...")
    web.run_app(app, port=8080)
