
from services.classroom_service import list_courses, get_course_materials
from aiogram import Router, types, F
from services.classroom_service import get_course_materials, list_courses
from services.google_auth import get_credentials
from keyboards.role_keyboard import user_roles

import logging
logging.basicConfig(level=logging.INFO)

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

def student_menu():
    buttons = [
        [types.KeyboardButton(text="Курсы")],
        [types.KeyboardButton(text="Просмотр материалов")],
        [types.KeyboardButton(text="🔙 Выйти")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@router.callback_query(F.data == "role_student")
async def student_handler(callback: types.CallbackQuery):
    user_roles[callback.from_user.id] = "student"  # Сохраняем роль
    await callback.message.answer("🎓 Вы вошли как студент.", reply_markup=student_menu())

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
        await state.clear()  # Сбрасываем состояние
        return

    # Отправляем материалы
    text = f"📖 *Материалы курса {selected_course}:*\n\n"
    for material in materials:
        print(material)
        # Заголовок материала
        text += f"🔹 *{material['title']}*\n"
        
        # Описание материала (если есть)
        if 'description' in material:
            text += f"📜 *Описание:* {material['description']}\n"
        
        # Вложения (если есть)
        if 'attachments' in material:
            text += "📎 *Вложения:*\n"
            for attachment in material['attachments']:
                text += f"  - {attachment['title']} (ID: {attachment['file_id']})\n"
        
        # Разделитель между материалами
        text += "\n"

    await message.answer(text, parse_mode="Markdown")
    await state.clear()  # Сбрасываем состояние

