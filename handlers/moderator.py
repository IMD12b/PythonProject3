# handlers/moderator.py
from aiogram import Router, F, Bot                  # ← добавили Bot
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.memory_db import get_all_couriers, get_courier_by_id, update_courier_status
from keyboard.courer_key import courier_main_kb

moderator_router = Router()


@moderator_router.message(F.text == "👥 Заявки на модерацию")
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