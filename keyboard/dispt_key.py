from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def admin_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Создать заказ")],
            [KeyboardButton(text="📊 Все заказы")],
            [KeyboardButton(text="Назначить")],
            [KeyboardButton(text="👥 Список курьеров")]
        ],
        resize_keyboard=True
    )

def admin_target_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назначить ")],
            [KeyboardButton(text="📊 Все заказы")],
            [KeyboardButton(text="Назначить")],
            [KeyboardButton(text="👥 Список курьеров")]
        ],
        resize_keyboard=True
    )

def order_cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

def order_confirm_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Сохранить")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )