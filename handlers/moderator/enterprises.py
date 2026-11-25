# handlers/moderator/enterprises.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.enterprises import add_enterprise, get_all_enterprises
from db.geocoder import get_coordinates
from filtres.is_moderator import IsModerator
from config import MODERATOR_IDS
from keyboard.moderator_key import moderator_main_kb, enterprises_kb

moderator_enterprises_router = Router()


class EnterpriseCreation(StatesGroup):
    waiting_name = State()
    waiting_address = State()


@moderator_enterprises_router.message(
    F.text == "🏭 Предприятия",
    IsModerator(moderator_ids=MODERATOR_IDS),
)
async def show_enterprises(message: Message):
    ents = await get_all_enterprises()
    if not ents:
        return await message.answer(
            "Предприятий пока нет.\nНажмите «➕ Добавить предприятие», чтобы создать.",
            reply_markup=enterprises_kb(),
        )
    text = "🏭 <b>Предприятия:</b>\n\n"
    for e in ents:
        text += f"• <b>{e['name']}</b>\n  {e['address']}\n  ({e['lat']:.4f}, {e['lon']:.4f})\n\n"
    await message.answer(text, parse_mode="HTML",
                         reply_markup=enterprises_kb(),)


@moderator_enterprises_router.message(
    F.text == "➕ Добавить предприятие",
    IsModerator(moderator_ids=MODERATOR_IDS),
)
async def start_add_enterprise(message: Message, state: FSMContext):
    await state.set_state(EnterpriseCreation.waiting_name)
    await message.answer("Введите <b>название предприятия</b>:", parse_mode="HTML")


@moderator_enterprises_router.message(EnterpriseCreation.waiting_name, F.text)
async def process_enterprise_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(EnterpriseCreation.waiting_address)
    await message.answer("Введите <b>адрес предприятия</b> (город, улица, дом):", parse_mode="HTML")


@moderator_enterprises_router.message(EnterpriseCreation.waiting_address, F.text)
async def process_enterprise_address(message: Message, state: FSMContext):
    address = message.text.strip()
    # геокодинг синхронный — выносим в поток, чтобы не блокировать loop
    import asyncio
    coords = await asyncio.to_thread(get_coordinates, address)

    if not coords:
        return await message.answer(
            "❌ Не удалось найти адрес на карте. Введите более точный адрес."
        )

    lat, lon = coords
    data = await state.get_data()
    ent_id = await add_enterprise(data["name"], address, lat, lon)
    await state.clear()

    await message.answer(
        f"✅ Предприятие <b>{data['name']}</b> создано (ID: {ent_id}).\n"
        f"📍 {address}\n"
        f"Координаты: {lat:.4f}, {lon:.4f}",
        reply_markup=moderator_main_kb(),
        parse_mode="HTML",
    )
@moderator_enterprises_router.message(F.text == "⬅️ Назад")
async def back_to_moderator_menu(message: Message):
    await message.answer("Главное меню модератора.", reply_markup=moderator_main_kb())