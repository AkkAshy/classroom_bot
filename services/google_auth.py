# import os
# import pickle
# import logging

# import aiohttp
# import aiohttp.web as web

# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow

# # Настройки авторизации
# SCOPES = [
#     "https://www.googleapis.com/auth/classroom.courses",
#     "https://www.googleapis.com/auth/classroom.coursework.students",
#     "https://www.googleapis.com/auth/classroom.coursework.me",
#     "https://www.googleapis.com/auth/classroom.announcements",
#     "https://www.googleapis.com/auth/classroom.rosters",
#     "https://www.googleapis.com/auth/classroom.courses.readonly",
#     "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly"
# ]
# TOKEN_DIR = "tokens"  # Папка для хранения токенов
# CREDENTIALS_PATH = "services/credentials.json"  # Файл с Google API ключами

# # Создаём папку для токенов, если её нет
# if not os.path.exists(TOKEN_DIR):
#     os.makedirs(TOKEN_DIR)

# def get_token_path(user_id):
#     """Возвращает путь к токену пользователя."""
#     return os.path.join(TOKEN_DIR, f"{user_id}.pickle")

# async def handle_auth_request(request):
#     """Обработчик запроса на авторизацию."""
#     user_id = request.query.get("user_id")
#     if not user_id:
#         return web.json_response({"error": "user_id is required"}, status=400)

#     creds, auth_url = get_credentials(user_id)

#     if auth_url:
#         return web.json_response({"auth_url": auth_url})
#     else:
#         return web.json_response({"error": "Failed to generate auth URL"}, status=500)


# def get_credentials(user_id):
#     """Получает учетные данные Google API для конкретного пользователя."""
#     logging.info(f"🚀 Запуск авторизации для пользователя {user_id}...")

#     creds = None  # Храним объект Credentials
#     auth_url = None  # Ссылка на авторизацию
#     token_path = get_token_path(user_id)  # Путь к персональному токену

#     # Проверяем, есть ли сохранённый токен
#     if os.path.exists(token_path):
#         logging.info(f"📂 Найден {token_path}, загружаем...")
#         with open(token_path, 'rb') as token:
#             try:
#                 creds = pickle.load(token)
#                 if not isinstance(creds, Credentials):  # Проверяем тип
#                     logging.error("❌ Ошибка! Загруженные данные не являются объектом Credentials.")
#                     creds = None  # Обнуляем, чтобы вызвать авторизацию заново
#             except Exception as e:
#                 logging.error(f"❌ Ошибка загрузки токена: {e}")
#                 creds = None  # Обнуляем, если что-то пошло не так

#     # Проверяем валидность токена
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             logging.info("🔄 Токен устарел, обновляем...")
#             creds.refresh(Request())
#         else:
#             if not os.path.exists(CREDENTIALS_PATH):
#                 logging.error(f"❌ Ошибка! Файл {CREDENTIALS_PATH} не найден.")
#                 return None, None  # Вернём два значения: нет токена и нет ссылки

#             logging.info("🔑 Новый вход. Откройте ссылку для авторизации...")
#             flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
#             auth_url, _ = flow.authorization_url(prompt="consent")  # Берём первую часть

#             creds = flow.run_local_server(port=8080, open_browser=True) 
#             print("DEBUG: Жду авторизацию...") # Ожидаем подтверждения в браузере

#         # Сохраняем токен
#         if creds and isinstance(creds, Credentials):
#             logging.info(f"💾 Сохраняем токен в {token_path}...")
#             with open(token_path, 'wb') as token_file:
#                 pickle.dump(creds, token_file)
#             logging.info("✅ Токен успешно сохранён!")
#     print(auth_url, "DEBUG: auth_url from get_credentials")
#     return creds, auth_url  # Возвращаем объект Credentials и ссылку

# def get_url(user_id):
#     print(get_credentials(user_id=user_id))

# if __name__ == "__main__":
#     auth_url = get_credentials()
#     if auth_url:
#         logging.info("🎉 Авторизация успешна!")
#     else:
#         logging.error("❌ Авторизация не удалась!")


import os
import pickle
import logging
from aiohttp import web
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Получаем значения из переменных окружения
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")



SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/classroom.coursework.students",
    "https://www.googleapis.com/auth/classroom.coursework.me",
    "https://www.googleapis.com/auth/classroom.announcements",
    "https://www.googleapis.com/auth/classroom.rosters",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly",
    "https://www.googleapis.com/auth/forms.body",
    "openid"
]

TOKEN_DIR = "tokens"
# CREDENTIALS_PATH = "services/credentials.json"

if not os.path.exists(TOKEN_DIR):
    os.makedirs(TOKEN_DIR)

def get_token_path(user_id):
    """Путь к токену пользователя."""
    return os.path.join(TOKEN_DIR, f"{user_id}.pickle")



async def get_credentials(user_id):
    """Асинхронная версия получения токена."""
    logging.info(f"🚀 Авторизация для {user_id}...")
    creds = None
    auth_url = None
    token_path = get_token_path(user_id)

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            try:
                creds = pickle.load(token)
                if not isinstance(creds, Credentials):
                    creds = None
            except Exception as e:
                logging.error(f"❌ Ошибка загрузки токена: {e}")
                creds = None

    if not creds or not creds.valid:
        if creds and creds.expired:
            if creds.refresh_token:
                logging.info("🔄 Токен устарел, обновляем...")
                creds.refresh(Request())
            else:
                logging.error("❌ Токен истёк, но отсутствует refresh_token. Требуется повторный логин.")
                creds = None

        if creds is None:
            if not CLIENT_ID or not CLIENT_SECRET:
                logging.error(f"❌ Не найдены переменные окружения для клиента.")
                return None, None
            
            # Создаем новый вход с использованием данных из переменных окружения
            logging.info("🔑 Новый вход. Открываем ссылку...")
            flow = InstalledAppFlow.from_client_config(
                {
                    "web": {
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["https://classroom-bot-7wn6.onrender.com/oauth_callback"]
                    }
                },
                SCOPES,
            )
            flow.redirect_uri = "https://classroom-bot-7wn6.onrender.com/oauth_callback"
            logging.info(f"Flow config: {flow}")
            logging.info(f"Redirect URI: {flow.redirect_uri}")

            auth_url, _ = flow.authorization_url(prompt="consent", state=user_id)
            print(auth_url, "DEBUG: auth_url from get_credentials")

    if creds and creds.valid:
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
            logging.info(f"✔️ Токен сохранён в {token_path}")
    
    return creds, auth_url


# async def get_credentials(user_id):
#     """Асинхронная версия получения токена."""
#     logging.info(f"🚀 Авторизация для {user_id}...")
#     creds = None
#     auth_url = None
#     token_path = get_token_path(user_id)

#     if os.path.exists(token_path):
#         with open(token_path, 'rb') as token:
#             try:
#                 creds = pickle.load(token)
#                 if not isinstance(creds, Credentials):
#                     creds = None
#             except Exception as e:
#                 logging.error(f"❌ Ошибка загрузки токена: {e}")
#                 creds = None

#     if not creds or not creds.valid:
#         if creds and creds.expired:
#             if creds.refresh_token:
#                 logging.info("🔄 Токен устарел, обновляем...")
#                 creds.refresh(Request())
#             else:
#                 logging.error("❌ Токен истёк, но отсутствует refresh_token. Требуется повторный логин.")
#                 creds = None

#         if creds is None:
#             if not os.path.exists(CREDENTIALS_PATH):
#                 logging.error(f"❌ Файл {CREDENTIALS_PATH} не найден.")
#                 return None, None
            
#             logging.info("🔑 Новый вход. Открываем ссылку...")
#             flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
#             flow.redirect_uri = "http://localhost:8080/oauth_callback"
#             auth_url, _ = flow.authorization_url(prompt="consent", state=user_id)
    
#     return creds, auth_url

async def handle_auth_request(request):
    """Запрос на авторизацию."""
    user_id = request.query.get("user_id")
    if not user_id:
        return web.json_response({"error": "user_id is required"}, status=400)
    
    _, auth_url = await get_credentials(user_id)
    if auth_url:
        return web.json_response({"auth_url": auth_url})
    else:
        return web.json_response({"error": "Failed to generate auth URL"}, status=500)

async def handle_oauth_callback(request):
    """Обработчик Google OAuth callback."""
    user_id = request.query.get("state")
    code = request.query.get("code")
    if not user_id or not code:
        return web.json_response({"error": "Missing user_id or code"}, status=400)
    
    flow = InstalledAppFlow.from_client_config(
                {
                    "web": {
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["https://classroom-bot-7wn6.onrender.com/oauth_callback"]
                    }
                },
                SCOPES,
            )
    flow.redirect_uri = "https://classroom-bot-7wn6.onrender.com/oauth_callback"

    try:
        flow.fetch_token(code=code)
        creds = flow.credentials

        token_path = get_token_path(user_id)
        with open(token_path, 'wb') as token_file:
            pickle.dump(creds, token_file)

        return web.json_response({"message": "Authorization successful!"})

    except Exception as e:
        logging.error(f"❌ Ошибка при получении токена: {e}")
        return web.json_response({"error": f"Ошибка при получении токена: {str(e)}"}, status=500)

def get_url(user_id):

    return f"https://classroom-bot-7wn6.onrender.com/auth?user_id={user_id}"

