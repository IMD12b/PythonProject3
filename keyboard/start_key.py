from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def role_selection_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛵 Я Курьер")],
            [KeyboardButton(text="💼 Я Диспетчер")]
        ],
        resize_keyboard=True
    )