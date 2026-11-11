# handlers/moderator/couriers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.memory_db import (
    get_all_couriers, get_courier_by_id, get_courier_shifts,
    update_courier_status,
)

mod_couriers_router = Router()


@mod_couriers_router.message(F.text == "📋 Список курьеров")
async def show_couriers_list(message: Message):
    couriers = await get_all_couriers()
    if not couriers:
        return await message.answer("В базе нет курьеров.")

    builder = InlineKeyboardBuilder()
    for c in couriers:
        builder.button(text=c["name"], callback_data=f"manage_courier:{c['id']}")
    builder.adjust(1)
    await message.answer("Выбери курьера для управления:", reply_markup=builder.as_markup())


@mod_couriers_router.callback_query(F.data.startswith("manage_courier:"))
async def manage_courier(callback: CallbackQuery):
    courier_id = int(callback.data.split(":")[1])
    courier = await get_courier_by_id(courier_id)
    shifts = await get_courier_shifts(courier_id)

    shifts_text = "\n".join([f"• {s['start']} — {s['end']}" for s in shifts]) if shifts else "График пуст."
    text = f"👤 <b>{courier['name']}</b>\nСтатус: {courier['status']}\n\n🗓 <b>График:</b>\n{shifts_text}"

    builder = InlineKeyboardBuilder()
    # ВАЖНО: три части в callback_data — set_shift:courier:<id>
    builder.button(text="➕ Добавить смену", callback_data=f"set_shift:courier:{courier_id}")
    if courier["status"] != "rejected":
        builder.button(text="❌ Уволить", callback_data=f"fire_courier:{courier_id}")
    builder.button(text="⬅️ Назад", callback_data="back_to_couriers")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@mod_couriers_router.callback_query(F.data == "back_to_couriers")
async def back_to_couriers(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()


@mod_couriers_router.callback_query(F.data.startswith("fire_courier:"))
async def fire_courier(callback: CallbackQuery):
    courier_id = int(callback.data.split(":")[1])
    await update_courier_status(courier_id, "rejected")
    await callback.message.edit_text("❌ Курьер уволен (доступ к заказам закрыт).")
    await callback.answer()