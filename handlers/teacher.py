from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.classroom_service import add_material_to_course, list_courses, create_course # Функции API Classroom
from services.google_auth import get_credentials  # Функция авторизации
from keyboards.role_keyboard import user_roles


router = Router()

class MaterialState(StatesGroup):
    waiting_for_course = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_attachment = State()
    waiting_for_text = State()
    waiting_for_course_name = State()

# 📌 Главное меню учителя
def teacher_menu():
    buttons = [
        [KeyboardButton(text="Добавить материал")],
        [KeyboardButton(text="📚 Мои курсы")],
        [KeyboardButton(text="➕ Создать курс")],
        [KeyboardButton(text="🔙 Выйти")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# 📌 Обработчик входа учителя
@router.callback_query(F.data == "role_teacher")
async def teacher_handler(callback: types.CallbackQuery):
    user_roles[callback.from_user.id] = "teacher"  # Сохраняем роль
    await callback.message.answer("🎓 Вы вошли как учитель.", reply_markup=teacher_menu())
    


# 📌 Обработчик команды для добавления материала
@router.message(F.text == "Добавить материал")
async def start_adding_material(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    courses = await list_courses(user_id=user_id)  # Получаем список курсов

    if not courses:
        await message.answer("❌ У вас нет доступных курсов.")
        return

    # Создаём кнопки для выбора курса
    
    buttons = [[KeyboardButton(text=course["name"])] for course in courses]
    markup = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    await message.answer("📌 Выберите курс, в который хотите добавить материал:", reply_markup=markup)
    await state.set_state(MaterialState.waiting_for_course)

@router.message(MaterialState.waiting_for_course)
async def receive_course_selection(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    selected_course = message.text.strip()
    courses = await list_courses(user_id=user_id)
    course_id = next((c["id"] for c in courses if c["name"] == selected_course), None)

    if not course_id:
        await message.answer("❌ Ошибка: выбранный курс не найден. Попробуйте снова.")
        return

    await state.update_data(course_id=course_id, user_id=user_id)
    await message.answer("📌 Введите название материала:")
    await state.set_state(MaterialState.waiting_for_title)

@router.message(MaterialState.waiting_for_title)
async def receive_material_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    await state.update_data(title=title)
    
    await message.answer("✍️ Теперь введите описание материала:")
    await state.set_state(MaterialState.waiting_for_description)

@router.message(MaterialState.waiting_for_description)
async def receive_material_description(message: types.Message, state: FSMContext):
    description = message.text.strip()
    await state.update_data(description=description)
    
    await message.answer("📎 Прикрепите файл или отправьте ссылку (если нет, напишите 'нет'):")
    await state.set_state(MaterialState.waiting_for_attachment)

@router.message(MaterialState.waiting_for_attachment)
async def receive_material_attachment(message: types.Message, state: FSMContext):
    
    data = await state.get_data()
    user_id = data.get("user_id")
    course_id = data.get("course_id")
    title = data.get("title")
    description = data.get("description")

    # Проверяем, текст это или файл
    if message.text:
        attachment = message.text.strip() if message.text.lower() != "нет" else None
    elif message.document:  # Если отправили файл
        attachment = message.document.file_id
    elif message.photo:  # Если отправили фото
        attachment = message.photo[-1].file_id
    else:
        attachment = None  # Если ничего не было отправлено

    success = await add_material_to_course(user_id, course_id, title, description, attachment)

    if success:
        await message.answer("✅ Материал успешно добавлен в курс!", reply_markup=teacher_menu())
    else:
        await message.answer("❌ Ошибка при добавлении материала.")

    await state.clear()



# 📌 Обработчик выбора курса
@router.message(MaterialState.waiting_for_course)
async def receive_course_selection(message: types.Message, state: FSMContext):
    selected_course = message.text.strip()
    courses = await list_courses()

    # Проверяем, существует ли курс
    course_id = next((c["id"] for c in courses if c["name"] == selected_course), None)
    
    if not course_id:
        await message.answer("❌ Ошибка: выбранный курс не найден. Попробуйте снова.")
        return

    await state.update_data(course_id=course_id)
    await message.answer("✍️ Теперь введите текст материала:")
    await state.set_state(MaterialState.waiting_for_text)

# 📌 Обработчик ввода текста
@router.message(MaterialState.waiting_for_text)
async def receive_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    course_id = data.get("course_id")
    text = message.text.strip()

    if not course_id:
        await message.answer("❌ Ошибка: курс не выбран. Попробуйте снова.")
        await state.clear()
        return

    success = add_material_to_course(course_id, text)

    if success:
        await message.answer("✅ Материал успешно добавлен в курс!", reply_markup=teacher_menu())
    else:
        await message.answer("❌ Ошибка при добавлении материала.")

    await state.clear()


@router.message(F.text == "📚 Мои курсы")  # Отлавливаем нажатие кнопки
async def show_courses(message: types.Message):
    user_id = message.from_user.id
    courses = await list_courses(user_id)  # Получаем список курсов

    if not courses:
        await message.answer("❌ У вас нет доступных курсов.")
        return

    text = "📚 *Ваши курсы:*\n\n"
    for course in courses:
        text += f"📌 *{course['name']}*\n"

    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "➕ Создать курс")
async def create_course_start(message: types.Message, state: FSMContext):
    await message.answer("📌 Введите название нового курса:")
    await state.set_state(MaterialState.waiting_for_course_name)

@router.message(MaterialState.waiting_for_course_name)
async def create_course_finish(message: types.Message, state: FSMContext):
    course_name = message.text.strip()

    if not course_name:
        await message.answer("❌ Название курса не может быть пустым. Попробуйте снова.")
        return

    success = await create_course(course_name)

    if success:
        await message.answer(f"✅ Курс *{course_name}* успешно создан!", parse_mode="Markdown", reply_markup=teacher_menu())
    else:
        await message.answer("❌ Ошибка при создании курса. Попробуйте позже.")

    await state.clear()