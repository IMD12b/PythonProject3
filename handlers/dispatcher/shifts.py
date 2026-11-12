from aiogram import Router, F
from aiogram.types import Message

from db.dispatcher_shifts import start_dispatcher_shift_log, end_dispatcher_shift_log
from db.memory_db import (
    get_dispatcher_by_tg_id, get_dispatcher_shifts,
    is_dispatcher_on_shift, toggle_dispatcher_shift_status,
)

dispatcher_shifts_router = Router()
@dispatcher_shifts_router.message(F.text == "⏱ Закончить/Начать смену")
async def toggle_disp_shift(message: Message):
    disp = await get_dispatcher_by_tg_id(message.from_user.id)
    if not disp: return await message.answer("Тебя нет в базе.")

    if not disp["is_on_shift"]:
        if not await is_dispatcher_on_shift(disp["id"]):
            return await message.answer("⛔ Сейчас не твое время по графику.")
        await toggle_dispatcher_shift_status(disp["id"], True)
        await start_dispatcher_shift_log(disp["id"])
        await message.answer("🟢 Смена начата!")
    else:
        await toggle_dispatcher_shift_status(disp["id"], False)
        await end_dispatcher_shift_log(disp["id"])
        await message.answer("🔴 Смена завершена.")


@dispatcher_shifts_router.message(F.text == "🗓 Мои Смены")
async def show_my_dispatcher_shifts(message: Message):
    disp = await get_dispatcher_by_tg_id(message.from_user.id)
    if not disp:
        return await message.answer("Тебя нет в базе диспетчеров.")

    shifts = await get_dispatcher_shifts(disp["id"])

    if not shifts:
        return await message.answer("У тебя пока нет назначенных смен. Обратись к модератору.")

    text = "🗓 <b>Твой график смен:</b>\n\n"
    for s in shifts:
        text += f"• {s['start']} — {s['end']}\n"

    if await is_dispatcher_on_shift(disp["id"]):
        text += "\n🟢 <b>Сейчас твоя смена активна.</b>"
    else:
        text += "\n🔴 <b>Сейчас не твое время работы.</b>"

    await message.answer(text, parse_mode="HTML")
