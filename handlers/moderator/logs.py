# handlers/moderator/logs.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.memory_db import (
    get_courier_by_id, get_dispatcher_by_id,
    get_courier_shift_logs, get_dispatcher_shift_logs,
)

mod_logs_router = Router()


@mod_logs_router.callback_query(F.data.startswith("view_logs:"))
async def view_logs(callback: CallbackQuery):
    # Формат: "view_logs:courier:5" или "view_logs:dispatcher:3"
    _, role, obj_id_str = callback.data.split(":")
    obj_id = int(obj_id_str)

    if role == "courier":
        obj = await get_courier_by_id(obj_id)
        logs = await get_courier_shift_logs(obj_id, limit=20)
        title = f"📜 Логи смен курьера <b>{obj['name']}</b>"
    else:
        obj = await get_dispatcher_by_id(obj_id)
        logs = await get_dispatcher_shift_logs(obj_id, limit=20)
        title = f"📜 Логи смен диспетчера <b>{obj['name']}</b>"

    if not logs:
        return await callback.message.answer(f"{title}\n\nЛогов пока нет.")

    lines = [title, ""]
    for log in logs:
        clock_in = log["clock_in"].strftime("%Y-%m-%d %H:%M") if log["clock_in"] else "—"
        clock_out = log["clock_out"].strftime("%Y-%m-%d %H:%M") if log["clock_out"] else "🟢 ещё на смене"
        lines.append(f"• {clock_in} → {clock_out}")

    text = "\n".join(lines)

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data=f"manage_{role}:{obj_id}")
    builder.adjust(1)

    await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()