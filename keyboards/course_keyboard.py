from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def course_keyboard(courses):
    """Создаёт клавиатуру с курсами"""
    keyboard = InlineKeyboardMarkup()
    for course in courses:
        keyboard.add(InlineKeyboardButton(course['name'], callback_data=f"course_{course['id']}"))
    return keyboard
