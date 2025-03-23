from aiogram import types, Router
from aiogram.filters import Command  # 👈 Добавляем импорт
from services.classroom_service import list_courses
from keyboards.course_keyboard import course_keyboard

router = Router()  # 👈 Используем router вместо Dispatcher

@router.message(Command("courses"))  # 👈 Используем новый синтаксис Aiogram 3.x
async def show_courses(message: types.Message):
    """Выводит список курсов пользователя"""
    user_id = message.from_user.id  # 👈 Получаем ID пользователя
    courses = list_courses(user_id)  # 👈 Теперь передаём ID

    if not courses:
        await message.answer("❌ У вас нет курсов в Google Classroom.")
        return

    await message.answer("📚 Выберите курс:", reply_markup=course_keyboard(courses))

@router.callback_query(lambda c: c.data.startswith("course_"))  # 👈 Регистрируем callback
async def select_course(callback_query: types.CallbackQuery):
    """Обрабатывает выбор курса"""
    course_id = callback_query.data.split("_")[1]
    await callback_query.message.answer(f"✅ Курс выбран! ID: {course_id}")
    await callback_query.answer()  # Закрываем уведомление

