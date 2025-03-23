from googleapiclient.discovery import build
from services.google_auth import get_credentials  # Функция авторизации
from googleapiclient.errors import HttpError
import pickle
import os
import asyncio
import logging

TOKEN_DIR = "tokens"

logger = logging.getLogger(__name__)  # Создаем логгер


def get_stored_credentials(user_id):
    token_file = f"{TOKEN_DIR}/{user_id}.pickle"

    if not os.path.exists(token_file):
        return None  # Токены не найдены

    with open(token_file, "rb") as token:
        creds = pickle.load(token)

    return creds

async def get_classroom_service(user_id):
    """Асинхронно создаёт и возвращает сервис Google Classroom с обработкой ошибок."""
    creds = await get_credentials(user_id=user_id)
    if not creds:
        logger.error("❌ Не удалось получить токен доступа!")
        return None

    for attempt in range(3):  # Повторяем попытки 3 раза
        try:
            creds, _ = await get_credentials(user_id=user_id)  # Получаем только учетные данные, игнорируем auth_url
            service = build("classroom", "v1", credentials=creds)  # ✅ Исправлено

            logger.info("✅ Подключение к Google Classroom API успешно!")
            return service
        except HttpError as error:
            logger.error(f"❌ Ошибка подключения (попытка {attempt + 1}/3): {error}")
            await asyncio.sleep(2)  # Даем API время восстановиться перед новой попыткой

    logger.critical("🚨 Все попытки подключения к Google Classroom API не удались.")
    return None

async def list_courses(user_id):
    """Получает список курсов, в которых записан ученик"""
    creds = get_stored_credentials(user_id)
    if not creds:
        print(f"❌ У пользователя {user_id} нет сохранённых токенов.")
        return []  

    service = build("classroom", "v1", credentials=creds)

    try:
        response = service.courses().list().execute()
        courses = response.get("courses", [])

        # Отладочный вывод (посмотри в консоли)
        print(f"📚 Найденные курсы для {user_id}: {courses}")

        return [{"id": c["id"], "name": c["name"]} for c in courses]
    
    except HttpError as e:
        print(f"❌ Ошибка при получении курсов для {user_id}: {e}")
        return []




async def add_material_to_course(user_id, course_id: str, title: str, description: str, attachment: str = None):
    """Асинхронно добавляет материал в курс Google Classroom."""
    service = await get_classroom_service(user_id=user_id)  # Должно быть await

    if not service:
        return False

    announcement = {
        "courseId": course_id,
        "text": f"{title}\n\n{description}" if description else title,
    }

    if attachment:
        announcement["materials"] = [{"link": {"url": attachment}}]

    try:
        service.courses().announcements().create(courseId=course_id, body=announcement).execute()  # Убрал await
        return True
    except HttpError as error:
        logger.error(f"❌ Ошибка при добавлении материала: {error}")
        return False


    

async def create_course(name, user_id):
    """Асинхронное создание нового курса в Google Classroom"""
    creds = get_credentials(user_id=user_id)  # Убедись, что get_credentials() НЕ асинхронная!
    
    if not creds:
        return False  # Ошибка авторизации
    
    try:
        service = build("classroom", "v1", credentials=creds)

        course_data = {
            "name": name,
            "ownerId": "me",
            "courseState": "ACTIVE"
        }

        course = service.courses().create(body=course_data).execute()
        return course  # Успешно созданный курс
    except HttpError as error:
        print(f"❌ Ошибка при создании курса: {error}")
        return False



async def get_course_materials(course_id, user_id):
    """Получает список материалов курса"""
    creds = get_stored_credentials(user_id)
    if not creds:
        return []  # Если токенов нет, возвращаем пустой список

    service = build("classroom", "v1", credentials=creds)

    try:
        response = service.courses().courseWork().list(courseId=course_id).execute()
        materials = response.get("courseWork", [])

        if not materials:
            print(f"❌ В курсе {course_id} нет доступных материалов.")
            return []

        result = []

        for material in materials:
            item = {
                "title": material["title"],
                "description": material.get("description", "Нет описания"),
                "attachments": []
            }

            # Проверяем вложения
            if "materials" in material:
                for attachment in material["materials"]:
                    if "driveFile" in attachment:
                        file_info = attachment["driveFile"]
                        item["attachments"].append({
                            "title": file_info["title"],
                            "file_id": file_info["id"]
                        })
                    elif "link" in attachment:
                        item["attachments"].append({
                            "title": "Ссылка",
                            "url": attachment["link"]["url"]
                        })
                    elif "youtubeVideo" in attachment:
                        item["attachments"].append({
                            "title": "YouTube Видео",
                            "url": f"https://www.youtube.com/watch?v={attachment['youtubeVideo']['id']}"
                        })

            result.append(item)

        return result
    except HttpError as e:
        print(f"Ошибка при получении материалов: {e}")
        return []



from googleapiclient.discovery import build

def get_email(creds):
    """Пытается получить email пользователя через Google People API"""
    try:
        people_service = build("people", "v1", credentials=creds)
        profile = people_service.people().get(resourceName="people/me", personFields="emailAddresses").execute()

        user_email = profile.get("emailAddresses", [{}])[0].get("value", None)
        if user_email:
            return user_email
        else:
            return "❌ Email не найден, проверь права доступа."
    except Exception as e:
        return f"❌ Ошибка при получении email: {e}"


async def enroll_user_to_course(user_id, course_id):
    """Добавляет пользователя в курс по его user_id и course_id"""
    creds = get_stored_credentials(user_id) 
     
    if not creds:
        return {"success": False, "error": "❌ У вас нет сохранённого токена."}

    service = build("classroom", "v1", credentials=creds)

    try:
        response = service.userProfiles().get(userId="me").execute()
        print("Google API Response:", response)  # Выведет полный ответ API

        user_email = get_email(creds)
        # response.get("emailAddress", None) 
        # if not user_email:
        #     return {"success": False, "error": "❌ Google API не вернул emailAddress. Проверь токен и разрешения."}

        user_email = service.userProfiles().get(userId="me").execute()["emailAddress"]

        enrollment = {
            "userId": user_email  # Google Classroom требует email, а не user_id
        }

        service.courses().students().create(courseId=course_id, body=enrollment).execute()
        return {"success": True, "message": "✅ Вы успешно записаны в курс!"}
    
    except HttpError as e:
        error_message = str(e)
        if "409" in error_message:
            return {"success": False, "error": "⚠️ Вы уже записаны в этот курс."}
        elif "403" in error_message:
            return {"success": False, "error": "❌ У вас нет прав для записи в курс."}
        elif "404" in error_message:
            return {"success": False, "error": "❌ Курс не найден. Проверьте код курса."}
        else:
            return {"success": False, "error": f"❌ Ошибка: {error_message}"}
