# handlers/moderator/shifts.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from datetime import datetime, timedelta

from db.memory_db import (add_shift, add_dispatcher_shift,
    get_shift_by_id, update_shift, delete_shift,
    get_dispatcher_shift_by_id, update_dispatcher_shift, delete_dispatcher_shift,
    )

mod_shifts_router = Router()


class ShiftEdit(StatesGroup):
    waiting_date = State()
    waiting_start = State()
    waiting_end = State()


# 1. Старт — открыть календарь
@mod_shifts_router.callback_query(F.data.startswith("set_shift:"))
async def start_set_shift(callback: CallbackQuery, state: FSMContext):
    # Формат: "set_shift:courier:123" или "set_shift:dispatcher:456"
    _, role, obj_id_str = callback.data.split(":")
    obj_id = int(obj_id_str)

    await state.update_data(role=role, obj_id=obj_id)

    calendar = SimpleCalendar(locale="ru_RU")
    await callback.message.edit_text(
        f"🗓 Выбери дату смены для {'Курьера' if role == 'courier' else 'Диспетчера'}:",
        reply_markup=await calendar.start_calendar(),
        parse_mode="HTML"
    )
    await state.set_state(ShiftEdit.waiting_date)
    await callback.answer()


# 2. Выбор даты
@mod_shifts_router.callback_query(ShiftEdit.waiting_date, SimpleCalendarCallback.filter())
async def process_shift_date(callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    calendar = SimpleCalendar(locale="ru_RU")
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
@mod_shifts_router.callback_query(ShiftEdit.waiting_start, F.data.startswith("shift_start:"))
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


# 4. Выбор конца и сохранение
@mod_shifts_router.callback_query(ShiftEdit.waiting_end, F.data.startswith("shift_end:"))
async def process_shift_end_time(callback: CallbackQuery, state: FSMContext):
    end_time = callback.data.replace("shift_end:", "")
    data = await state.get_data()

    role = data["role"]
    obj_id = data["obj_id"]
    edit_shift_id = data.get("edit_shift_id")      # ← читаем
    shift_date = data["shift_date"]
    shift_start = data["shift_start"]

    full_start = f"{shift_date} {shift_start}"

    if end_time == "00:00":
        next_day = datetime.strptime(shift_date, "%Y-%m-%d") + timedelta(days=1)
        full_end = f"{next_day.strftime('%Y-%m-%d')} {end_time}"
    else:
        full_end = f"{shift_date} {end_time}"

    role_name = "Курьера" if role == "courier" else "Диспетчера"

    if edit_shift_id:
        # ── РЕДАКТИРОВАНИЕ ──
        if role == "courier":
            ok = await update_shift(edit_shift_id, full_start, full_end)
        else:
            ok = await update_dispatcher_shift(edit_shift_id, full_start, full_end)

        if not ok:
            await state.clear()
            await callback.message.edit_text("⚠️ Не удалось обновить смену (не найдена).")
            return await callback.answer()

        result_text = f"✅ Смена для {role_name} обновлена:\nС: {full_start}\nПо: {full_end}"
    else:
        # ── СОЗДАНИЕ ──
        if role == "courier":
            await add_shift(obj_id, full_start, full_end)
        else:
            await add_dispatcher_shift(obj_id, full_start, full_end)
        result_text = f"✅ Смена для {role_name} добавлена:\nС: {full_start}\nПо: {full_end}"

    await state.clear()
    await callback.message.edit_text(result_text, parse_mode="HTML")
    await callback.answer("Сохранено!")
# ---------- РЕДАКТИРОВАНИЕ СМЕНЫ ----------

@mod_shifts_router.callback_query(F.data.startswith("edit_shift:"))
async def start_edit_shift(callback: CallbackQuery, state: FSMContext):
    _, role, shift_id_str = callback.data.split(":")
    shift_id = int(shift_id_str)

    if role == "courier":
        shift = await get_shift_by_id(shift_id)
        obj_id = shift["courier_id"] if shift else None
    else:
        shift = await get_dispatcher_shift_by_id(shift_id)
        obj_id = shift["dispatcher_id"] if shift else None

    if not shift or obj_id is None:
        return await callback.answer("Смена не найдена", show_alert=True)

    await state.update_data(role=role, obj_id=obj_id, edit_shift_id=shift_id)   # ← ключевое

    calendar = SimpleCalendar(locale="ru_RU")
    await callback.message.edit_text(
        "✏️ Редактирование смены. Выбери новую дату:",
        reply_markup=await calendar.start_calendar(),
        parse_mode="HTML"
    )
    await state.set_state(ShiftEdit.waiting_date)
    await callback.answer()



# ---------- УДАЛЕНИЕ СМЕНЫ: ПОДТВЕРЖДЕНИЕ ----------

@mod_shifts_router.callback_query(F.data.startswith("delete_shift:"))
async def confirm_delete_shift(callback: CallbackQuery):
    # Формат: "delete_shift:courier:5" или "delete_shift:dispatcher:5"
    _, role, shift_id_str = callback.data.split(":")
    shift_id = int(shift_id_str)

    if role == "courier":
        shift = await get_shift_by_id(shift_id)
    else:
        shift = await get_dispatcher_shift_by_id(shift_id)

    if not shift:
        return await callback.answer("Смена не найдена", show_alert=True)

    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Да, удалить", callback_data=f"confirm_delete_shift:{role}:{shift_id}")
    builder.button(text="❌ Отмена", callback_data="cancel_delete_shift")
    builder.adjust(2)

    await callback.message.edit_text(
        f"Удалить смену?\n\nС: {shift['start']}\nПо: {shift['end']}",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@mod_shifts_router.callback_query(F.data == "cancel_delete_shift")
async def cancel_delete_shift(callback: CallbackQuery):
    await callback.message.edit_text("Удаление отменено.")
    await callback.answer()


# ---------- УДАЛЕНИЕ СМЕНЫ: САМО УДАЛЕНИЕ ----------

@mod_shifts_router.callback_query(F.data.startswith("confirm_delete_shift:"))
async def do_delete_shift(callback: CallbackQuery):
    _, role, shift_id_str = callback.data.split(":")
    shift_id = int(shift_id_str)

    if role == "courier":
        ok = await delete_shift(shift_id)
    else:
        ok = await delete_dispatcher_shift(shift_id)

    if ok:
        await callback.message.edit_text("🗑 Смена удалена.")
    else:
        await callback.message.edit_text("⚠️ Не удалось удалить смену (не найдена).")
    await callback.answer()