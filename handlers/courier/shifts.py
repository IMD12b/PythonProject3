from aiogram import Router, F
from aiogram.types import Message

from db.courier_shift import start_courier_shift_log, end_courier_shift_log
from db.memory_db import (
    get_courier_by_tg_id, get_courier_shifts,
    is_courier_on_shift, toggle_courier_shift_status,
)

courier_shifts_router = Router()
@courier_shifts_router.message(F.text == "🗓 Мои смены")
async def show_my_shifts(message: Message):
    courier = await get_courier_by_tg_id(message.from_user.id)
    if not courier:
        return await message.answer("Тебя нет в базе.")

    # Берем список смен из новой таблицы
    shifts = await get_courier_shifts(courier["id"])

    if not shifts:
        return await message.answer("У тебя пока нет назначенных смен. Обратись к модератору.")

    text = "🗓 <b>Твой график смен:</b>\n\n"
    for s in shifts:
        text += f"• {s['start']} — {s['end']}\n"

    # Проверяем, идет ли сейчас смена
    if await is_courier_on_shift(courier["id"]):
        text += "\n🟢 <b>Сейчас твоя смена активна.</b>"
    else:
        text += "\n🔴 <b>Сейчас не твое время работы.</b>"

    await message.answer(text, parse_mode="HTML")


@courier_shifts_router.message(F.text == "⏱ Начать/Закончить смену")
async def toggle_shift(message: Message):
    courier = await get_courier_by_tg_id(message.from_user.id)
    if not courier: return await message.answer("Тебя нет в базе.")

    if not courier["is_on_shift"]:
        if not await is_courier_on_shift(courier["id"]):
            return await message.answer("⛔ Сейчас не твое время по графику.")
        await toggle_courier_shift_status(courier["id"], True)
        await start_courier_shift_log(courier["id"])
        await message.answer("🟢 Смена начата!")
    else:
        await toggle_courier_shift_status(courier["id"], False)
        await end_courier_shift_log(courier["id"])
        await message.answer("🔴 Смена завершена.")