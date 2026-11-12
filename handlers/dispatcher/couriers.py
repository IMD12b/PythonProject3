from aiogram import Router, F
from aiogram.types import Message

from db.memory_db import get_all_couriers

dispatcher_couriers_router = Router()
@dispatcher_couriers_router.message(F.text == "👥 Список курьеров")
async def show_all_couriers_for_admin(message: Message):
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