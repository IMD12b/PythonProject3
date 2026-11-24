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
    active_couriers = [c for c in couriers if c["status"] != "rejected"]

    if not active_couriers:
        return await message.answer("В базе нет активных курьеров.")

    builder = InlineKeyboardBuilder()
    for c in active_couriers:
        builder.button(text=c["name"], callback_data=f"manage_courier:{c['id']}")
    builder.adjust(1)
    await message.answer("Выбери курьера для управления:", reply_markup=builder.as_markup())


@mod_couriers_router.callback_query(F.data.startswith("manage_courier:"))
async def manage_courier(callback: CallbackQuery):
    courier_id = int(callback.data.split(":")[1])
    courier = await get_courier_by_id(courier_id)
    shifts = await get_courier_shifts(courier_id)

    # 1. Карточка курьера
    text = f"👤 <b>{courier['name']}</b>\nСтатус: {courier['status']}"
    await callback.message.edit_text(text, parse_mode="HTML")

    # 2. Кнопка «Добавить смену» + «Логи»
    top = InlineKeyboardBuilder()
    top.button(text="➕ Добавить смену", callback_data=f"set_shift:courier:{courier_id}")
    await callback.message.answer("Управление сменами:", reply_markup=top.as_markup())

    # 3. Каждая смена — отдельным сообщением с ✏️ и 🗑
    if not shifts:
        await callback.message.answer("График пуст.")
    else:
        for s in shifts:
            b = InlineKeyboardBuilder()
            b.button(text="✏️ Редактировать", callback_data=f"edit_shift:courier:{s['id']}")
            b.button(text="🗑 Удалить", callback_data=f"delete_shift:courier:{s['id']}")
            b.adjust(2)
            await callback.message.answer(
                f"• {s['start']} — {s['end']}",
                reply_markup=b.as_markup()
            )

    # 4. Уволить / Назад
    bottom = InlineKeyboardBuilder()
    if courier["status"] != "rejected":
        bottom.button(text="❌ Уволить", callback_data=f"fire_courier:{courier_id}")
    bottom.button(text="⬅️ Назад", callback_data="back_to_couriers")
    bottom.adjust(1)
    await callback.message.answer("Действия:", reply_markup=bottom.as_markup())
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