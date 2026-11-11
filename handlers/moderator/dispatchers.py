# handlers/moderator/dispatchers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.memory_db import (
    get_all_dispatchers, get_dispatcher_by_id, get_dispatcher_shifts,
    update_dispatcher_status,
)

mod_dispatchers_router = Router()


@mod_dispatchers_router.message(F.text == "💼 список диспетчеров")
async def show_dispatchers_list(message: Message):
    dispatchers = await get_all_dispatchers()
    if not dispatchers:
        return await message.answer("В базе нет диспетчеров.")

    builder = InlineKeyboardBuilder()
    for d in dispatchers:
        builder.button(text=d["name"], callback_data=f"manage_dispatcher:{d['id']}")
    builder.adjust(1)
    await message.answer("Выбери диспетчера для управления:", reply_markup=builder.as_markup())


@mod_dispatchers_router.callback_query(F.data.startswith("manage_dispatcher:"))
async def manage_dispatcher(callback: CallbackQuery):
    disp_id = int(callback.data.split(":")[1])
    dispatcher = await get_dispatcher_by_id(disp_id)
    shifts = await get_dispatcher_shifts(disp_id)

    shifts_text = "\n".join([f"• {s['start']} — {s['end']}" for s in shifts]) if shifts else "График пуст."
    text = f"💼 <b>{dispatcher['name']}</b>\nСтатус: {dispatcher['status']}\n\n🗓 <b>График:</b>\n{shifts_text}"

    builder = InlineKeyboardBuilder()
    # Здесь уже было правильно: set_shift:dispatcher:<id>
    builder.button(text="➕ Добавить смену", callback_data=f"set_shift:dispatcher:{disp_id}")
    if dispatcher["status"] != "rejected":
        builder.button(text="❌ Уволить", callback_data=f"fire_dispatcher:{disp_id}")
    builder.button(text="⬅️ Назад", callback_data="back_to_dispatchers")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@mod_dispatchers_router.callback_query(F.data == "back_to_dispatchers")
async def back_to_dispatchers(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()


@mod_dispatchers_router.callback_query(F.data.startswith("fire_dispatcher:"))
async def fire_dispatcher(callback: CallbackQuery):
    disp_id = int(callback.data.split(":")[1])
    await update_dispatcher_status(disp_id, "rejected")
    await callback.message.edit_text("❌ Диспетчер уволен.")
    await callback.answer()