# handlers/moderator.py
from aiogram import Router, F, Bot                  # ← добавили Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.memory_db import (get_all_couriers, get_courier_by_id, update_courier_status, add_shift, get_courier_shifts,get_all_dispatchers, get_dispatcher_by_id, update_dispatcher_status,
    add_dispatcher_shift, get_dispatcher_shifts)
from keyboard.courer_key import courier_main_kb
from keyboard.dispt_key import admin_main_kb
from keyboard.moderator_key import moderator_main_kb
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from datetime import datetime, timedelta


moderator_router = Router()

class ShiftEdit(StatesGroup):
    waiting_date = State()
    waiting_start = State()
    waiting_end = State()


@moderator_router.message(F.text == "💼 список диспетчеров")
async def show_dispatchers_list(message: Message):
    dispatchers = await get_all_dispatchers()
    if not dispatchers: return await message.answer("В базе нет диспетчеров.")

    builder = InlineKeyboardBuilder()
    for d in dispatchers:
        builder.button(text=d["name"], callback_data=f"manage_dispatcher:{d['id']}")
    builder.adjust(1)
    await message.answer("Выбери диспетчера для управления:", reply_markup=builder.as_markup())


@moderator_router.callback_query(F.data.startswith("manage_dispatcher:"))
async def manage_dispatcher(callback: CallbackQuery):
    disp_id = int(callback.data.split(":")[1])
    dispatcher = await get_dispatcher_by_id(disp_id)
    shifts = await get_dispatcher_shifts(disp_id)

    shifts_text = "\n".join([f"• {s['start']} — {s['end']}" for s in shifts]) if shifts else "График пуст."
    text = f"💼 <b>{dispatcher['name']}</b>\nСтатус: {dispatcher['status']}\n\n🗓 <b>График:</b>\n{shifts_text}"

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить смену", callback_data=f"set_shift:dispatcher:{disp_id}")
    if dispatcher['status'] != 'rejected':
        builder.button(text="❌ Уволить", callback_data=f"fire_dispatcher:{disp_id}")
    builder.button(text="⬅️ Назад", callback_data="back_to_dispatchers")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@moderator_router.callback_query(F.data == "back_to_dispatchers")
async def back_to_dispatchers(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

@moderator_router.callback_query(F.data.startswith("fire_dispatcher:"))
async def fire_dispatcher(callback: CallbackQuery):
    disp_id = int(callback.data.split(":")[1])
    await update_dispatcher_status(disp_id, "rejected")
    await callback.message.edit_text("❌ Диспетчер уволен.")
    await callback.answer()


@moderator_router.message(F.text == "📋 Список курьеров")
async def show_couriers_list(message: Message):
    couriers = await get_all_couriers()
    if not couriers: return await message.answer("В базе нет курьеров.")

    builder = InlineKeyboardBuilder()
    for c in couriers: builder.button(text=c["name"], callback_data=f"manage_courier:{c['id']}")
    builder.adjust(1)
    await message.answer("Выбери курьера для управления:", reply_markup=builder.as_markup())


@moderator_router.callback_query(F.data.startswith("manage_courier:"))
async def manage_courier(callback: CallbackQuery):
    courier_id = int(callback.data.split(":")[1])
    courier = await get_courier_by_id(courier_id)
    shifts = await get_courier_shifts(courier_id)

    shifts_text = "\n".join([f"• {s['start']} — {s['end']}" for s in shifts]) if shifts else "График пуст."
    text = f"👤 <b>{courier['name']}</b>\nСтатус: {courier['status']}\n\n🗓 <b>График:</b>\n{shifts_text}"

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить смену", callback_data=f"set_shift:{courier_id}")
    if courier['status'] != 'rejected': builder.button(text="❌ Уволить", callback_data=f"fire_courier:{courier_id}")
    builder.button(text="⬅️ Назад", callback_data="back_to_couriers")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@moderator_router.callback_query(F.data == "back_to_couriers")
async def back_to_couriers(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()


@moderator_router.callback_query(F.data.startswith("set_shift:"))
async def start_set_shift(callback: CallbackQuery, state: FSMContext):
    # Формат callback_data: "set_shift:courier:123" или "set_shift:dispatcher:456"
    _, role, obj_id_str = callback.data.split(":")
    obj_id = int(obj_id_str)

    await state.update_data(role=role, obj_id=obj_id)

    calendar = SimpleCalendar(locale='ru_RU')
    await callback.message.edit_text(
        f"🗓 Выбери дату смены для {'Курьера' if role == 'courier' else 'Диспетчера'}:",
        reply_markup=await calendar.start_calendar(),
        parse_mode="HTML"
    )
    await state.set_state(ShiftEdit.waiting_date)
    await callback.answer()


# 2. Выбор даты
@moderator_router.callback_query(ShiftEdit.waiting_date, SimpleCalendarCallback.filter())
async def process_shift_date(callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    calendar = SimpleCalendar(locale='ru_RU')
    selected, date = await calendar.process_selection(callback, callback_data)

    if selected:
        selected_date = date.strftime("%Y-%m-%d")
        await state.update_data(shift_date=selected_date)

        builder = InlineKeyboardBuilder()
        for hour in range(8, 23, 2):
            time_str = f"{hour:02d}:00"
            builder.button(text=time_str, callback_data=f"shift_start:{time_str}")
        builder.adjust(3)

        await callback.message.edit_text(
            f"Дата: <b>{selected_date}</b>\nТеперь выбери время <b>НАЧАЛА</b> смены:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await state.set_state(ShiftEdit.waiting_start)
    await callback.answer()


# 3. Выбор начала
@moderator_router.callback_query(ShiftEdit.waiting_start, F.data.startswith("shift_start:"))
async def process_shift_start_time(callback: CallbackQuery, state: FSMContext):
    start_time = callback.data.replace("shift_start:", "")
    await state.update_data(shift_start=start_time)

    builder = InlineKeyboardBuilder()
    for hour in range(10, 25, 2):
        time_str = "00:00" if hour == 24 else f"{hour:02d}:00"
        builder.button(text=time_str, callback_data=f"shift_end:{time_str}")
    builder.adjust(3)

    await callback.message.edit_text(
        f"Начало: <b>{start_time}</b>\nТеперь выбери время <b>КОНЦА</b> смены:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(ShiftEdit.waiting_end)
    await callback.answer()


# 4. Выбор конца и СОХРАНЕНИЕ
@moderator_router.callback_query(ShiftEdit.waiting_end, F.data.startswith("shift_end:"))
async def process_shift_end_time(callback: CallbackQuery, state: FSMContext):
    end_time = callback.data.replace("shift_end:", "")
    data = await state.get_data()

    role = data["role"]
    obj_id = data["obj_id"]
    shift_date = data["shift_date"]
    shift_start = data["shift_start"]

    full_start = f"{shift_date} {shift_start}"

    if end_time == "00:00":
        next_day = datetime.strptime(shift_date, "%Y-%m-%d") + timedelta(days=1)
        full_end = f"{next_day.strftime('%Y-%m-%d')} {end_time}"
    else:
        full_end = f"{shift_date} {end_time}"

    # УНИВЕРСАЛЬНОЕ СОХРАНЕНИЕ
    if role == "courier":
        await add_shift(obj_id, full_start, full_end)
        role_name = "Курьера"
    else:
        await add_dispatcher_shift(obj_id, full_start, full_end)
        role_name = "Диспетчера"

    await state.clear()
    await callback.message.edit_text(
        f"✅ Смена для {role_name} добавлена:\nС: {full_start}\nПо: {full_end}",
        parse_mode="HTML"
    )
    await callback.answer("Смена сохранена!")


@moderator_router.callback_query(F.data.startswith("fire_courier:"))
async def fire_courier(callback: CallbackQuery):
    courier_id = int(callback.data.split(":")[1])
    await update_courier_status(courier_id, "rejected")
    await callback.message.edit_text("❌ Курьер уволен (доступ к заказам закрыт).")
    await callback.answer()




@moderator_router.message(F.text == "👥 Заявки курьеров")
async def show_couriers_menu(message: Message):
    couriers = await get_all_couriers()              # ← await
    pending_couriers = [c for c in couriers if c["status"] == "pending"]

    if not pending_couriers:
        return await message.answer("Нет новых заявок.")

    for courier in pending_couriers:
        text = f"👤 <b>{courier['name']}</b>\n📞 {courier['phone']}"
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Принять", callback_data=f"mod_approve:{courier['id']}")
        builder.button(text="❌ Отклонить", callback_data=f"mod_reject:{courier['id']}")
        builder.adjust(2)
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@moderator_router.callback_query(F.data.startswith("mod_approve:"))
async def approve_courier(callback: CallbackQuery, bot: Bot):
    courier_id = int(callback.data.split(":")[1])
    courier = await get_courier_by_id(courier_id)    # ← await

    if await update_courier_status(courier_id, "approved"):   # ← await
        await callback.message.edit_text(f"✅ Курьер {courier['name']} принят.")

        try:
            await bot.send_message(
                chat_id=courier["telegram_id"],
                text="🎉 Поздравляем! Твоя заявка одобрена. Теперь ты можешь брать заказы.",
                reply_markup=courier_main_kb()
            )
        except Exception as e:
            await callback.message.answer(f"⚠️ Не удалось уведомить курьера: {e}")
    await callback.answer()


@moderator_router.callback_query(F.data.startswith("mod_reject:"))
async def reject_courier(callback: CallbackQuery, bot: Bot):
    courier_id = int(callback.data.split(":")[1])
    courier = await get_courier_by_id(courier_id)    # ← await

    if await update_courier_status(courier_id, "rejected"):   # ← await
        await callback.message.edit_text(f"❌ Курьер {courier['name']} отклонен.")

        try:
            await bot.send_message(
                chat_id=courier["telegram_id"],
                text="❌ К сожалению, твоя заявка отклонена."
            )
        except Exception:
            pass
    await callback.answer()


@moderator_router.message(F.text == "💼 Заявки диспетчеров")
async def show_pending_dispatchers(message: Message):
    dispatchers = await get_all_dispatchers()
    pending = [d for d in dispatchers if d["status"] == "pending"]
    if not pending: return await message.answer("Нет заявок от диспетчеров.")

    for d in pending:
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Принять", callback_data=f"disp_approve:{d['id']}")
        builder.button(text="❌ Отклонить", callback_data=f"disp_reject:{d['id']}")
        await message.answer(f"💼 <b>{d['name']}</b>\n📞 {d['phone']}", reply_markup=builder.as_markup(), parse_mode="HTML")

@moderator_router.callback_query(F.data.startswith("disp_approve:"))
async def approve_dispatcher(callback: CallbackQuery, bot: Bot):
    disp_id = int(callback.data.split(":")[1])
    dispatcher = await get_dispatcher_by_id(disp_id)
    if await update_dispatcher_status(disp_id, "approved"):
        await callback.message.edit_text(f"✅ Диспетчер {dispatcher['name']} принят.")
        try:
            await bot.send_message(
                dispatcher["telegram_id"],
                "🎉 Твоя заявка одобрена. Ты вошел как Диспетчер.",
                reply_markup=admin_main_kb()
            )
        except Exception: pass
    await callback.answer()

@moderator_router.callback_query(F.data.startswith("disp_reject:"))
async def reject_dispatcher(callback: CallbackQuery, bot: Bot):
    disp_id = int(callback.data.split(":")[1])
    if await update_dispatcher_status(disp_id, "rejected"):
        await callback.message.edit_text("❌ Диспетчер отклонен.")
    await callback.answer()