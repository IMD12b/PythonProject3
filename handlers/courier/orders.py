from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.memory_db import (
    get_available_orders, get_courier_by_tg_id,
    assign_courier, get_orders_by_courier,
    complete_order, cancel_order, get_order_by_id,
)

courier_orders_router = Router()
@courier_orders_router.message(F.text == "🚚 Мой заказ")
async def show_my_order(message: Message):
    courier = await get_courier_by_tg_id(message.from_user.id)

    if not courier:
        return await message.answer("Ты не зарегистрирован как курьер.")

    if not courier["is_on_shift"]:
        return await message.answer("⛔ Ты не на смене.")

    orders = await get_orders_by_courier(courier["id"])
    active_order = next((o for o in orders if o["status"] == "🚚 В пути"), None)

    if not active_order:
        return await message.answer("У тебя нет активных заказов.")

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Доставлено", callback_data=f"complete_order:{active_order['id']}")   # ← исправлено
    builder.button(text="❌ Отказаться", callback_data=f"courier_cancel:{active_order['id']}")
    builder.adjust(2)
    clean_phone = "".join(c for c in active_order["client_phone"] if c.isdigit() or c == "+")

    # Создаем ссылку
    phone_text = f'📞 Клиент: <code>{active_order["client_phone"]}</code>'

    await message.answer(
        f"🚚 <b>Твой текущий заказ #{active_order['id']}</b>\n\n"
        f"📍 {active_order['address']}\n"
        f"👤 {active_order['client_name']}\n"
        f"{phone_text}",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@courier_orders_router.callback_query(F.data.startswith("take_order:"))
async def process_take_order(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    courier = await get_courier_by_tg_id(callback.from_user.id)

    if await assign_courier(order_id, courier["id"]):
        order = await get_order_by_id(order_id)

        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Доставлено", callback_data=f"complete_order:{order_id}")       # ← исправлено
        builder.button(text="❌ Отказаться", callback_data=f"courier_cancel:{order_id}")
        builder.adjust(2)

        phone_link = f'<a href="tel:{order["client_phone"]}">📞 Позвонить: {order["client_phone"]}</a>'

        await callback.message.edit_text(
            f"✅ Заказ #{order_id} закреплен за тобой.\n\n"
            f"📍 {order['address']}\n"
            f"👤 {order['client_name']}\n"
            f"{phone_link}\n\n"
            f"Когда доставишь - нажми кнопку.",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    else:
        await callback.answer("Не удалось взять заказ.", show_alert=True)

@courier_orders_router.callback_query(F.data.startswith("complete_order:"))
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


@courier_orders_router.callback_query(F.data.startswith("courier_cancel:"))
async def process_courier_cancel(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])

    if await cancel_order(order_id, reason="Отказ курьера"):
        await callback.message.edit_text(f"Заказ #{order_id} отменен и возвращен в пул.")
        await callback.answer("Ты отказался от заказа")
