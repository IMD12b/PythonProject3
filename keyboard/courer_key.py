from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def courier_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚚 Мой заказ")],
            [KeyboardButton(text="🗓 Мои смены")],
            [KeyboardButton(text="📍 Гео", request_location=True)],
            [KeyboardButton(text="⏱ Начать/Закончить смену")]
        ],
        resize_keyboard=True
    )