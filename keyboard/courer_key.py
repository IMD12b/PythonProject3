from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def courier_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Доступные заказы")],
            [KeyboardButton(text="🚚 Мой заказ")],
            [KeyboardButton(text="📍 Гео", request_location=True)],
        ],
        resize_keyboard=True
    )