# handlers/start.py
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

from keyboard.courer_key import courier_main_kb
from keyboard.dispt_key import admin_main_kb
from keyboard.moderator_key import moderator_main_kb

from filtres.is_moderator import IsModerator
from filtres.dispt_id import IsAdmin

from memory_db import get_courier_by_tg_id, register_courier

from config import ADMIN_IDS, MODERATOR_IDS


class Registration(StatesGroup):
    waiting_name = State()
    waiting_phone = State()


print(f"админы {ADMIN_IDS}")
start_router = Router()

# 1. СТАРТ ДЛЯ АДМИНА
@start_router.message(CommandStart(), IsAdmin(admin_ids=ADMIN_IDS))
async def cmd_start_admin(message: Message):
    await message.answer(
        f"Привет, {message.from_user.full_name}!\n"
        "Ты вошел как Админ/Диспетчер.",
        reply_markup=admin_main_kb()
    )

@start_router.message(CommandStart(), IsModerator(moderator_ids=MODERATOR_IDS))
async def cmd_start_moderator(message: Message):
    await message.answer(
        "Привет! Ты вошел как Модератор.\n"
        "Твоя задача — проверять заявки курьеров.",
        reply_markup=moderator_main_kb()
    )

# 2. СТАРТ ДЛЯ КУРЬЕРА
async def cmd_start_courier(message: Message, state: FSMContext):
    tg_id = message.from_user.id

    # Проверяем, есть ли уже такой курьер в базе
    courier = get_courier_by_tg_id(tg_id)

    if courier:
        # Если курьер уже есть, смотрим его статус
        if courier["status"] == "approved":
            await message.answer(
                f"С возвращением, {courier['name']}!",
                reply_markup=courier_main_kb()
            )
        elif courier["status"] == "pending":
            await message.answer(
                "⏳ Твоя заявка еще на рассмотрении у диспетчера. Подожди немного."
            )
        elif courier["status"] == "rejected":
            await message.answer(
                "❌ Твоя заявка была отклонена диспетчером."
            )
        return  # Выходим, если курьер уже найден

    # Если курьера нет — начинаем регистрацию
    await state.set_state(Registration.waiting_name)
    await message.answer("Привет! Ты новый курьер. Как тебя зовут?")


# 3. Получаем имя
@start_router.message(Registration.waiting_name, F.text)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Registration.waiting_phone)

    # Просим телефон
    phone_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить телефон", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer("Отправь свой номер телефона:", reply_markup=phone_kb)


# 4. Получаем телефон и сохраняем
@start_router.message(Registration.waiting_phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data["name"]
    tg_id = message.from_user.id
    phone = message.contact.phone_number

    # Сохраняем в "базу"
    register_courier(tg_id, name, phone)
    await state.clear()

    # Возвращаем обычную клавиатуру (пока просто чтобы убрать кнопку контакта)
    await message.answer(
        "✅ Заявка отправлена!\n"
        "Ожидай, пока диспетчер одобрит твою кандидатуру. "
        "Мы напишем, когда все будет готово.",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Меню")]], resize_keyboard=True)
    )

