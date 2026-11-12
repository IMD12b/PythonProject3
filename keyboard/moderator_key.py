from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def moderator_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Заявки курьеров")],
            [KeyboardButton(text="💼 Заявки диспетчеров")],
            [KeyboardButton(text="📋 Список курьеров")],
            [KeyboardButton(text="💼 список диспетчеров")],
            [KeyboardButton(text="📈 Статистика")]
        ],
        resize_keyboard=True
    )