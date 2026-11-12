# handlers/moderator.py
from aiogram import Router,F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta



from db.stats import (
    get_couriers_stats_for_period,
    get_dispatchers_stats_for_period,
    get_orders_stats_for_period
)

mod_stats_router = Router()
# Состояния для статистики
class StatsState(StatesGroup):
    choosing_category = State()
    choosing_period = State()


# 1. ВЫБОР КАТЕГОРИИ
@mod_stats_router.message(F.text == "📈 Статистика")
async def stats_start(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="🛵 Курьеры", callback_data="stat_cat:couriers")
    builder.button(text="💼 Диспетчеры", callback_data="stat_cat:dispatchers")
    builder.button(text="📦 Заказы", callback_data="stat_cat:orders")
    builder.adjust(1)

    await message.answer("Что будем смотреть?", reply_markup=builder.as_markup())
    await state.set_state(StatsState.choosing_category)


# 2. ВЫБОР ПЕРИОДА
@mod_stats_router.callback_query(StatsState.choosing_category, F.data.startswith("stat_cat:"))
async def stats_choose_period(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":")[1]
    await state.update_data(category=category)

    builder = InlineKeyboardBuilder()
    builder.button(text="Сегодня", callback_data="stat_period:today")
    builder.button(text="За неделю", callback_data="stat_period:week")
    builder.button(text="За месяц", callback_data="stat_period:month")
    builder.adjust(3)

    await callback.message.edit_text("Выбери период:", reply_markup=builder.as_markup())
    await state.set_state(StatsState.choosing_period)
    await callback.answer()


# 3. ВЫВОД РЕЗУЛЬТАТА
@mod_stats_router.callback_query(StatsState.choosing_period, F.data.startswith("stat_period:"))
async def stats_show_result(callback: CallbackQuery, state: FSMContext):
    period = callback.data.split(":")[1]
    data = await state.get_data()
    category = data["category"]

    now = datetime.now()
    if period == "today":
        date_from = now.replace(hour=0, minute=0, second=0)
    elif period == "week":
        date_from = now - timedelta(days=7)
    else:
        date_from = now - timedelta(days=30)

    period_text = f"с {date_from.strftime('%d.%m')} по {now.strftime('%d.%m')}"
    text = ""

    if category == "couriers":
        stats = await get_couriers_stats_for_period(date_from, now)
        text = f"🛵 <b>Статистика курьеров ({period_text})</b>\n\n"
        if not stats:
            text += "Нет данных."
        for s in stats:
            text += f"👤 <b>{s['name']}</b>\n⏱ Часов: {s['hours']} | 📦 Заказов: {s['orders']}\n\n"

    elif category == "dispatchers":
        stats = await get_dispatchers_stats_for_period(date_from, now)
        text = f"💼 <b>Статистика диспетчеров ({period_text})</b>\n\n"
        if not stats:
            text += "Нет данных."
        for s in stats:
            text += f"👤 <b>{s['name']}</b>\n⏱ Часов: {s['hours']}\n\n"

    elif category == "orders":
        stats = await get_orders_stats_for_period(date_from, now)
        text = (
            f"📦 <b>Статистика заказов ({period_text})</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Доставлено: {stats['delivered']}\n"
            f"⚠️ В процессе (недоставленные): {stats['undelivered']}\n"
            f"❌ Отменено: {stats['cancelled']}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"Всего заказов: {stats['total']}"
        )

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.clear()
    await callback.answer()