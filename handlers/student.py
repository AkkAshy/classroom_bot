
from services.classroom_service import list_courses, get_course_materials
from aiogram import Router, types, F
from services.classroom_service import get_course_materials, list_courses, enroll_user_to_course
from services.google_auth import get_credentials
from keyboards.role_keyboard import user_roles
import pickle
import os

from googleapiclient.errors import HttpError



import logging
logging.basicConfig(level=logging.INFO)
TOKEN_DIR = "tokens"
router = Router()

# 📌 Главное меню ученика
# # 📌 Обработчик входа ученика



# # 📌 Обработчик просмотра курсов
# @router.message(F.text == "Курсы")
# async def show_student_courses(message: types.Message):
#     courses = await list_courses()
    
#     if not courses:
#         await message.answer("❌ У вас нет доступных курсов.")
#         return
    
#     text = "📚 *Ваши курсы:*\n\n"
#     for course in courses:
#         text += f"📌 *{course['name']}*\n"

#     await message.answer(text, parse_mode="Markdown")

# # 📌 Обработчик просмотра материалов
# @router.message(F.text == "Просмотр материалов")
# async def ask_for_course_selection(message: types.Message):
#     courses = await list_courses()

#     if not courses:
#         await message.answer("❌ У вас нет доступных курсов.")
#         return

#     buttons = [[types.KeyboardButton(text=course["name"])] for course in courses]
#     markup = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

#     await message.answer("📌 Выберите курс для просмотра материалов:", reply_markup=markup)

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# Определяем состояния
class StudentStates(StatesGroup):
    selecting_course = State()
    entering_course_code = State()
    

def get_stored_credentials(user_id):
    token_file = f"{TOKEN_DIR}/{user_id}.pickle"

    if not os.path.exists(token_file):
        return None  # Токены не найдены

    with open(token_file, "rb") as token:
        creds = pickle.load(token)

    return creds
def student_menu():
    buttons = [
        [types.KeyboardButton(text="Курсы")],
        [types.KeyboardButton(text="Просмотр материалов")],
        [types.KeyboardButton(text="🔙 Выйти")],
        [types.KeyboardButton(text="Записаться на курс")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@router.callback_query(F.data == "role_student")
async def student_handler(callback: types.CallbackQuery):
    user_roles[callback.from_user.id] = "student"  # Сохраняем роль
    await callback.message.answer("🎓 Вы вошли как студент.", reply_markup=student_menu())

# @router.message(F.text == "Курсы")
# async def join_course_prompt(message: types.Message, state: FSMContext):
#     """Запрашивает у ученика код курса"""
#     await message.answer("🔢 Введите код курса для подключения:")

#     await state.set_state(StudentStates.entering_course_code)



# @router.message(StudentStates.entering_course_code)
# async def join_course(message: types.Message, state: FSMContext):
#     """Подключает ученика к курсу по коду"""
#     user_id = message.from_user.id
#     course_code = message.text.strip()

#     creds = get_stored_credentials(user_id)
#     if not creds:
#         await message.answer("❌ У вас нет авторизации. Войдите через Google.")
#         await state.clear()
#         return
#     from googleapiclient.discovery import build
#     service = build("classroom", "v1", credentials=creds)

#     try:
#         # Добавляем ученика
#         service.courses().students().create(
#             courseId=course_code,
#             body={"userId": "me"}  # "me" – текущий пользователь
#         ).execute()

#         await message.answer("✅ Вы успешно присоединились к курсу!")
#     except HttpError as e:
#         if e.resp.status == 403:
#             await message.answer("❌ У вас нет прав на присоединение к этому курсу.")
#         elif e.resp.status == 404:
#             await message.answer("❌ Код курса не найден. Проверьте правильность ввода.")
#         else:
#             await message.answer(f"⚠ Ошибка: {e}")
#     finally:
#         await state.clear()




# 📌 Обработчик просмотра материалов
@router.message(F.text == "Просмотр материалов")
async def ask_for_course_selection(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    courses = await list_courses(user_id=user_id)

    if not courses:
        await message.answer("❌ У вас нет доступных курсов.")
        return

    buttons = [[types.KeyboardButton(text=course["name"])] for course in courses]
    markup = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    await message.answer("📌 Выберите курс для просмотра материалов:", reply_markup=markup)
    await state.set_state(StudentStates.selecting_course)  # Устанавливаем состояние

# 📌 Обработчик выбора курса
@router.message(StudentStates.selecting_course)
async def show_course_materials(message: types.Message, state: FSMContext):
    selected_course = message.text.strip()
    user_id = message.from_user.id
    courses = await list_courses(user_id=user_id)

    # Проверяем, существует ли выбранный курс
    course_id = next((c["id"] for c in courses if c["name"] == selected_course), None)

    if not course_id:
        await message.answer("❌ Ошибка: курс не найден. Попробуйте снова.")
        return

    # Получаем материалы курса
    materials = await get_course_materials(course_id, user_id)

    if not materials:
        await message.answer("📭 В этом курсе пока нет материалов.")
        await state.clear()
        return

    # Отправляем материалы частями
    text_parts = []
    current_text = f"📖 *Материалы курса {selected_course}:*\n\n"

    for material in materials:
        print(material)  # Отладочный вывод

        # Заголовок материала
        current_text += f"🔹 *{material['title']}*\n"

        # Описание материала (если есть)
        if 'description' in material:
            current_text += f"📜 *Описание:* {material['description']}\n"

        # Вложения (если есть)
        if material.get('attachments'):
            current_text += "📎 *Вложения:*\n"
            for attachment in material['attachments']:
                if "file_id" in attachment:
                    current_text += f"  - 📄 {attachment['title']} (ID: {attachment['file_id']})\n"
                elif "url" in attachment:
                    current_text += f"  - 🔗 [{attachment['title']}]({attachment['url']})\n"

        current_text += "\n"

        # Проверяем длину сообщения
        if len(current_text) > 3500:  # Оставляем запас до 4096 символов
            text_parts.append(current_text)
            current_text = ""

    if current_text:
        text_parts.append(current_text)

    # Отправляем части сообщений
    for part in text_parts:
        await message.answer(part, parse_mode="Markdown")

    await state.clear()  # Сбрасываем состояние



@router.message(F.text == "Записаться на курс")
async def ask_for_course_code(message: types.Message, state: FSMContext):
    await message.answer("🔢 Введите код курса:")
    await state.set_state(StudentStates.entering_course_code)

@router.message(StudentStates.entering_course_code)
async def enroll_to_course(message: types.Message, state: FSMContext):
    course_code = message.text.strip()
    user_id = message.from_user.id

    result = await enroll_user_to_course(user_id, course_code)
    
    if result["success"]:
        await message.answer(result["message"])
    else:
        await message.answer(result["error"])

    await state.clear()  # Сбрасываем состояние
