from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def moderator_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Заявки курьеров")],
            [KeyboardButton(text="💼 Заявки диспетчеров")],
            [KeyboardButton(text="📋 Список курьеров")],
            [KeyboardButton(text="💼 список диспетчеров")],
            [KeyboardButton(text="📈 Статистика")],
            [KeyboardButton(text="🏭 Предприятия")]
        ],
        resize_keyboard=True
    )
def enterprises_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить предприятие")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )