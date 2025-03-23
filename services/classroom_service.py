from googleapiclient.discovery import build
from services.google_auth import get_credentials  # Функция авторизации
from googleapiclient.errors import HttpError
from .google_auth import get_credentials  # Подключаем авторизацию
import asyncio
import logging


logger = logging.getLogger(__name__)  # Создаем логгер

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
    """Асинхронно получает список курсов пользователя"""
    service = await get_classroom_service(user_id=user_id)
    if not service:
        return []

    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(None, lambda: service.courses().list().execute())
    
    return response.get("courses", [])


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
    """Получает список материалов курса (объявлений)"""
    service = await get_classroom_service(user_id=user_id)

    try:
        # Получаем материалы курса
        response = service.courses().courseWorkMaterials().list(courseId=course_id).execute()
        print(response)
        
        # Проверка, что materials существуют в ответе
        materials = response.get("courseWorkMaterials", [])
        if not materials:
            print(f"Нет материалов для курса с ID {course_id}")
            return []

        result = []  # Массив для хранения материалов

        for material in materials:
            material_info = {}

            # Проверка на наличие title (название материала)
            if 'title' in material:
                material_info["title"] = material['title']
            
            # Проверка на наличие description (описание материала)
            if 'description' in material:
                material_info["description"] = material['description']

            # Проверка на наличие вложений (materials, attachments или других полей)
            if 'materials' in material:  # API Google использует 'materials', а не 'attachments'
                files = []
                for attachment in material['materials']:
                    if 'driveFile' in attachment:  # Проверяем наличие вложений в формате 'driveFile'
                        file_info = attachment['driveFile']
                        files.append({
                            "title": file_info.get("title", "Без названия"),  # Название файла
                            "file_id": file_info.get("id")  # ID файла
                        })
                if files:
                    material_info["attachments"] = files  # Добавляем файлы к материалу

            result.append(material_info)  # Добавляем материал в список

        return result  # Возвращаем список с материалами

    except Exception as e:
        print(f"Ошибка при получении материалов курса: {e}")  # Логируем ошибку
        return []  # Возвращаем пустой список при ошибке


