# handlers/courier.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.memory_db import (
    get_available_orders,
    get_courier_by_tg_id,
    assign_courier,
    get_orders_by_courier,
    complete_order,
    is_courier_on_shift,get_courier_shifts
)

courier_router = Router()




# =========================================================
# МОЙ ЗАКАЗ
# =========================================================

@courier_router.message(F.text == "🚚 Мой заказ")
async def show_my_order(message: Message):
    courier = await get_courier_by_tg_id(message.from_user.id)

    if not courier:
        return await message.answer("Ты не зарегистрирован как курьер.")

    if not await is_courier_on_shift(courier["id"]):
        return await message.answer("⛔ Сейчас не твое время работы. Заказы недоступны. Проверь свои смены.")

    orders = await get_orders_by_courier(courier["id"])
    active = [o for o in orders if o["status"] == "🚚 В пути"]

    if not active:
        return await message.answer("У тебя нет активных заказов.")

    for order in active:
        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ Завершить",
            callback_data=f"complete_order:{order['id']}"
        )
        await message.answer(
            f"📦 Заказ #{order['id']}\n"
            f"📍 Адрес: {order['address']}\n"
            f"👤 Клиент: {order['client_name']}\n"
            f"📞 Телефон: {order['client_phone']}\n"
            f"💰 Сумма: {order['price']} ₽",
            reply_markup=builder.as_markup()
        )


@courier_router.callback_query(F.data.startswith("complete_order:"))
async def process_complete_order(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])

    courier = await get_courier_by_tg_id(callback.from_user.id)

    if not courier:
        return await callback.answer("Ты не зарегистрирован как курьер.", show_alert=True)

    # Проверяем, что этот заказ действительно принадлежит этому курьеру
    orders = await get_orders_by_courier(courier["id"])
    if not any(o["id"] == order_id for o in orders):
        return await callback.answer("Это не твой заказ.", show_alert=True)

    success = await complete_order(order_id)

    if success:
        await callback.message.edit_text(
            f"✅ Заказ #{order_id} завершён.\n"
            f"Спасибо за работу!"
        )
        await callback.answer("Готово!")
    else:
        await callback.answer("Не удалось завершить заказ.", show_alert=True)


@courier_router.message(F.text == "🗓 Мои смены")
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