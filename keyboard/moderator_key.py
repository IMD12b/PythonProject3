from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def moderator_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Заявки на модерацию")]
        ],
        resize_keyboard=True
    )