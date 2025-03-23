from aiogram import Router, types, F
from aiogram.filters import Command
import logging
from keyboards.role_keyboard import role_keyboard # ✅ Теперь используется inline-клавиатура
from handlers.teacher import teacher_menu
from handlers.student import student_menu
from services.google_auth import get_credentials
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()
logging.basicConfig(level=logging.INFO)

user_roles = {}  # Хранение ролей пользователей

@router.message(Command("start"))
async def start_command(message: types.Message):
    """Отправляет приветствие и предлагает авторизоваться перед выбором роли"""
    creds, auth_url = get_credentials()  # 🔥 Получаем авторизационные данные
    
    if auth_url:
        # Если требуется авторизация, отправляем ссылку
        auth_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Войти через Google", url=auth_url)]
            ]
        )
        await message.answer(
            "👋 Привет! Прежде чем выбрать роль, вам нужно авторизоваться.\n"
            "Нажмите на кнопку ниже:", reply_markup=auth_keyboard
        )
    else:
        # Если уже авторизован, сразу отправляем выбор роли
        await message.answer("✅ Вы уже авторизованы! Выберите свою роль:", reply_markup=role_keyboard())
        # Now you can access creds here
        creds = creds  # or do something with creds
# @router.message(Command("start"))
# async def start_command(message: types.Message):
#     """Отправляет приветствие и предлагает авторизоваться перед выбором роли"""
#     creds, auth_url = get_credentials()  # 🔥 Получаем авторизационные данные
    
#     if auth_url:
#         # Если требуется авторизация, отправляем ссылку
#         auth_keyboard = InlineKeyboardMarkup(
#             inline_keyboard=[
#                 [InlineKeyboardButton(text="🔗 Войти через Google", url=auth_url)]
#             ]
#         )
#         await message.answer(
#             "👋 Привет! Прежде чем выбрать роль, вам нужно авторизоваться.\n"
#             "Нажмите на кнопку ниже:", reply_markup=auth_keyboard
#         )
#     else:
#         # Если уже авторизован, сразу отправляем выбор роли
#         await message.answer("✅ Вы уже авторизованы! Выберите свою роль:", reply_markup=role_keyboard())


@router.callback_query(F.data == "role_teacher")
async def teacher_handler(callback: types.CallbackQuery):
    """Устанавливает роль Учителя и отправляет меню учителя"""
    user_roles[callback.from_user.id] = "teacher"
    logging.info(f"✅ Пользователь {callback.from_user.id} выбрал роль: Учитель")

    
    await callback.message.edit_text("Вы выбрали роль: 👨‍🏫 Учитель.")
    await callback.message.answer("🔹 Главное меню учителя:", reply_markup=teacher_menu())

@router.callback_query(F.data == "role_student")
async def student_handler(callback: types.CallbackQuery):
    """Устанавливает роль Ученика и отправляет меню ученика"""
    user_roles[callback.from_user.id] = "student"
    logging.info(f"✅ Пользователь {callback.from_user.id} выбрал роль: Ученик")
    
    await callback.message.edit_text("Вы выбрали роль: 🎓 Ученик.")
    await callback.message.answer("🔹 Главное меню ученика:", reply_markup=student_menu())
