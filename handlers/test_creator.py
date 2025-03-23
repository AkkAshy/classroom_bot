from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiohttp
import json
import logging
import os
import pickle

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage


# from googleapiclient.discovery import build

logging.basicConfig(level=logging.INFO)

router = Router()

TOKEN_DIR = "tokens"
 # Google Apps Script URL

# 📌 Состояния FSM

class TestCreation(StatesGroup):
    waiting_for_title = State()
    waiting_for_question = State()
    waiting_for_options = State()
    waiting_for_correct_answer = State()
    waiting_for_next_question = State()


def get_stored_credentials(user_id):
    token_file = f"{TOKEN_DIR}/{user_id}.pickle"

    if not os.path.exists(token_file):
        return None  # Токены не найдены

    with open(token_file, "rb") as token:
        creds = pickle.load(token)

    return creds

# 📌 Начало создания теста
@router.message(F.text == "Создать тест")
async def start_test_creation(message: types.Message, state: FSMContext):
    await message.answer("📌 Введите название теста:")
    await state.set_state(TestCreation.waiting_for_title)

# 📌 Получаем название теста
@router.message(TestCreation.waiting_for_title)
async def get_test_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text, questions=[])
    await message.answer("✅ Название сохранено!\nТеперь введите первый вопрос:")
    await state.set_state(TestCreation.waiting_for_question)

# 📌 Получаем вопрос
@router.message(TestCreation.waiting_for_question)
async def get_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    questions.append({"question": message.text, "options": []})
    
    await state.update_data(questions=questions)
    await message.answer("✍️ Введите варианты ответа (через запятую):")
    await state.set_state(TestCreation.waiting_for_options)

# 📌 Получаем варианты ответов
@router.message(TestCreation.waiting_for_options)
async def get_options(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    options = [opt.strip() for opt in message.text.split(",")]

    questions[-1]["options"] = options
    await state.update_data(questions=questions)

    await message.answer(f"🔢 Введите номер правильного ответа (1-{len(options)}):")
    await state.set_state(TestCreation.waiting_for_correct_answer)

# 📌 Получаем правильный ответ
@router.message(TestCreation.waiting_for_correct_answer)
async def get_correct_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    text = message.text.strip()

    if text.isdigit():
        answer_index = int(text) - 1
        if 0 <= answer_index < len(questions[-1]["options"]):
            questions[-1]["answer"] = answer_index
            await state.update_data(questions=questions)

            await message.answer("✅ Вопрос добавлен!\n\n➕ Добавить ещё один вопрос? (Да/Нет)")
            await state.set_state(TestCreation.waiting_for_next_question)
            return  

    await message.answer("⚠️ Ошибка! Введите номер правильного ответа или 'нет', если хотите завершить тест.")

# 📌 Добавляем следующий вопрос или завершаем тест
@router.message(TestCreation.waiting_for_next_question)
async def add_next_question(message: types.Message, state: FSMContext):
    text = message.text.lower()

    if text == "да":
        await message.answer("✍️ Введите следующий вопрос:")
        await state.set_state(TestCreation.waiting_for_question)

    elif text == "нет":
        await finish_test(message, state)

# 📌 Завершаем тест
async def finish_test(message: types.Message, state: FSMContext):
    data = await state.get_data()
    test_title = data["title"]
    test_questions = data["questions"]

    await message.answer(f"📨 Отправляем тест '{test_title}' в Google Forms...")

    # 🔥 Загружаем токены
    user_id = message.from_user.id
    creds = get_stored_credentials(user_id)

    if not creds:
        await message.answer("⚠️ Ошибка! Вы не авторизованы в Google.")
        return
    
    from googleapiclient.discovery import build

    service = build("forms", "v1", credentials=creds)

    # 🔥 Создаём форму
    form = {
        "info": {
            "title": test_title
        }
    }
    result = service.forms().create(body=form).execute()
    form_id = result["formId"]

    # 🔥 Добавляем вопросы
    requests = []
    for q in test_questions:
        question_item = {
            "createItem": {
                "item": {
                    "title": q["question"],
                    "questionItem": {
                        "question": {
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [{"value": opt} for opt in q["options"]],
                                "shuffle": False,
                            }
                        }
                    }
                },
                "location": {"index": 0},
            }
        }
        requests.append(question_item)

    # 🔥 Отправляем вопросы в форму
    service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()

    # 📌 Отправляем ссылку на форму пользователю
    form_url = f"https://docs.google.com/forms/d/{form_id}/edit"
    await message.answer(f"✅ Тест создан! Вот ссылка: {form_url}")

    # Очистка состояния
    await state.clear()