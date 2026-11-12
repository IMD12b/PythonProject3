from aiogram import Router, F
from aiogram.types import Message

from db.dispatchers import get_dispatcher_by_tg_id
from db.memory_db import get_all_couriers

dispatcher_couriers_router = Router()
@dispatcher_couriers_router.message(F.text == "👥 Список курьеров")
async def show_all_couriers_for_admin(message: Message):
    disp = await get_dispatcher_by_tg_id(message.from_user.id)
    if not disp:
        return await message.answer("Тебя нет в базе.")

    if not disp["is_on_shift"]:
        return await message.answer("⛔ Ты не на смене! Нажми «Начать/Закончить смену», чтобы начать работу.")
    text = "👥 <b>Все курьеры в системе:</b>\n\n"
    couriers = await get_all_couriers()

    if not couriers:
        return await message.answer("В базе пока нет ни одного курьера.")


    for c in couriers:
        busy = "🚚 Везет заказ" if c['is_busy'] else "☕ Свободен"
        status = c['status']
        if status!="rejected":
            text += (
                f"👤 <b>{c['name']}</b> ({status})\n"
                f"📞 {c['phone']}\n"
                f"Статус: {busy}\n\n"
        )
    await message.answer(text, parse_mode="HTML")