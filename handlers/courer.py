# handlers/courier.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery

# Создаём роутер для курьеров
courier_router = Router()




# 1. Обработка кнопки "Доступные заказы"
@courier_router.message(F.text == "📋 Доступные заказы")
async def show_orders(message: Message):
    # Пока это тестовые данные. Позже мы будем брать их из БД.
    orders = [
        {"id": 42, "address": "ул. Ленина 5", "price": 500},
        {"id": 43, "address": "ул. Мира 12", "price": 750},
    ]

    await message.answer("🔄 Загружаем доступные заказы...")

    for order in orders:
        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ Взять заказ",
            callback_data=f"take_order:{order['id']}"
        )

        await message.answer(
            f"📦 Заказ #{order['id']}\n"
            f"📍 Адрес: {order['address']}\n"
            f"💰 Сумма: {order['price']} ₽",
            reply_markup=builder.as_markup()
        )


# 2. Обработка нажатия на Inline-кнопку "Взять заказ"
@courier_router.callback_query(F.data.startswith("take_order:"))
async def process_take_order(callback: CallbackQuery):
    # Достаём ID заказа из callback_data (например, из "take_order:42" получаем "42")
    order_id = callback.data.split(":")[1]

    # Отвечаем на callback, чтобы у пользователя пропали "часики" на кнопке
    await callback.answer(f"Ты взял заказ #{order_id}!")

    # Меняем текст сообщения
    await callback.message.edit_text(
        f"✅ Заказ #{order_id} закреплён за тобой.\n"
        f"Статус: В пути 🚚",
        reply_markup=None  # Убираем кнопку
    )