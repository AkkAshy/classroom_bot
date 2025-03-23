from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def role_keyboard():
    """Клавиатура для выбора роли"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍🏫 Учитель", callback_data="role_teacher")],
        [InlineKeyboardButton(text="🎓 Ученик", callback_data="role_student")]
    ])
    return keyboard


user_roles = {}  # Словарь для хранения ролей пользователей

