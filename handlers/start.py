# handlers/start.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from keyboard.courer_key import courier_main_kb
from keyboard.start_key import role_selection_kb
from keyboard.dispt_key import admin_main_kb
from keyboard.moderator_key import moderator_main_kb
from filtres.dispt_id import IsAdmin
from config import ADMIN_IDS, MODERATOR_IDS
from database.memory_db import (
    get_courier_by_tg_id, register_courier,
    get_dispatcher_by_tg_id, register_dispatcher
)

start_router = Router()


class Registration(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    choosing_role = State()  # Новое состояние для выбора


@start_router.message(CommandStart(), IsAdmin(admin_ids=ADMIN_IDS))
async def cmd_start_admin(message: Message):
    await message.answer("Ты вошел как Админ.", reply_markup=admin_main_kb())


@start_router.message(CommandStart(), F.from_user.id.in_(MODERATOR_IDS))
async def cmd_start_moderator(message: Message):
    await message.answer("Ты вошел как Модератор.", reply_markup=moderator_main_kb())


@start_router.message(CommandStart())
async def cmd_start_user(message: Message, state: FSMContext):
    # Проверяем, может он уже курьер?
    courier = await get_courier_by_tg_id(message.from_user.id)
    if courier:
        if courier["status"] == "approved":
            return await message.answer(f"С возвращением, {courier['name']}!", reply_markup=courier_main_kb())
        elif courier["status"] == "pending":
            return await message.answer("⏳ Твоя заявка (Курьер) на рассмотрении.")
        else:
            return await message.answer("❌ Твоя заявка (Курьер) отклонена.")

    # Проверяем, может он уже диспетчер?
    dispatcher = await get_dispatcher_by_tg_id(message.from_user.id)
    if dispatcher:
        if dispatcher["status"] == "approved":
            return await message.answer(f"С возвращением, {dispatcher['name']}!", reply_markup=admin_main_kb())
        elif dispatcher["status"] == "pending":
            return await message.answer("⏳ Твоя заявка (Диспетчер) на рассмотрении.")
        else:
            return await message.answer("❌ Твоя заявка (Диспетчер) отклонена.")

    # Если никого нет - предлагаем выбор
    await message.answer("Привет! Выбери, кем ты хочешь работать:", reply_markup=role_selection_kb())
    await state.set_state(Registration.choosing_role)


# Выбор Курьера
@start_router.message(Registration.choosing_role, F.text == "🛵 Я Курьер")
async def choose_courier(message: Message, state: FSMContext):
    await state.update_data(role="courier")
    await state.set_state(Registration.waiting_name)
    await message.answer("Введи свое имя:")


# Выбор Диспетчера
@start_router.message(Registration.choosing_role, F.text == "💼 Я Диспетчер")
async def choose_dispatcher(message: Message, state: FSMContext):
    await state.update_data(role="dispatcher")
    await state.set_state(Registration.waiting_name)
    await message.answer("Введи свое имя:")


# Получаем имя
@start_router.message(Registration.waiting_name, F.text)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Registration.waiting_phone)
    phone_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Отправить телефон", request_contact=True)]],
                                   resize_keyboard=True)
    await message.answer("Отправь свой номер телефона:", reply_markup=phone_kb)


# Получаем телефон и регистрируем
@start_router.message(Registration.waiting_phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("role")
    name = data["name"]
    tg_id = message.from_user.id
    phone = message.contact.phone_number

    if role == "courier":
        await register_courier(tg_id, name, phone)
    elif role == "dispatcher":
        await register_dispatcher(tg_id, name, phone)

    await state.clear()
    await message.answer(
        "✅ Заявка отправлена! Ожидай проверки модератора.",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Меню")]], resize_keyboard=True)
    )