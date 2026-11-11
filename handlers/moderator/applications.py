# handlers/moderator/applications.py
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.memory_db import (
    get_all_couriers, get_courier_by_id, update_courier_status,
    get_all_dispatchers, get_dispatcher_by_id, update_dispatcher_status,
)
from keyboard.courer_key import courier_main_kb
from keyboard.dispt_key import admin_main_kb

mod_applications_router = Router()


# ---------- ЗАЯВКИ КУРЬЕРОВ ----------

@mod_applications_router.message(F.text == "👥 Заявки курьеров")
async def show_couriers_menu(message: Message):
    couriers = await get_all_couriers()
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


@mod_applications_router.callback_query(F.data.startswith("mod_approve:"))
async def approve_courier(callback: CallbackQuery, bot: Bot):
    courier_id = int(callback.data.split(":")[1])
    courier = await get_courier_by_id(courier_id)

    if await update_courier_status(courier_id, "approved"):
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


@mod_applications_router.callback_query(F.data.startswith("mod_reject:"))
async def reject_courier(callback: CallbackQuery, bot: Bot):
    courier_id = int(callback.data.split(":")[1])
    courier = await get_courier_by_id(courier_id)

    if await update_courier_status(courier_id, "rejected"):
        await callback.message.edit_text(f"❌ Курьер {courier['name']} отклонен.")
        try:
            await bot.send_message(
                chat_id=courier["telegram_id"],
                text="❌ К сожалению, твоя заявка отклонена."
            )
        except Exception:
            pass
    await callback.answer()


# ---------- ЗАЯВКИ ДИСПЕТЧЕРОВ ----------

@mod_applications_router.message(F.text == "💼 Заявки диспетчеров")
async def show_pending_dispatchers(message: Message):
    dispatchers = await get_all_dispatchers()
    pending = [d for d in dispatchers if d["status"] == "pending"]

    if not pending:
        return await message.answer("Нет заявок от диспетчеров.")

    for d in pending:
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Принять", callback_data=f"disp_approve:{d['id']}")
        builder.button(text="❌ Отклонить", callback_data=f"disp_reject:{d['id']}")
        builder.adjust(2)
        await message.answer(
            f"💼 <b>{d['name']}</b>\n📞 {d['phone']}",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )


@mod_applications_router.callback_query(F.data.startswith("disp_approve:"))
async def approve_dispatcher(callback: CallbackQuery, bot: Bot):
    disp_id = int(callback.data.split(":")[1])
    dispatcher = await get_dispatcher_by_id(disp_id)

    if await update_dispatcher_status(disp_id, "approved"):
        await callback.message.edit_text(f"✅ Диспетчер {dispatcher['name']} принят.")
        try:
            await bot.send_message(
                chat_id=dispatcher["telegram_id"],
                text="🎉 Твоя заявка одобрена. Ты вошел как Диспетчер.",
                reply_markup=admin_main_kb()
            )
        except Exception:
            pass
    await callback.answer()


@mod_applications_router.callback_query(F.data.startswith("disp_reject:"))
async def reject_dispatcher(callback: CallbackQuery, bot: Bot):
    disp_id = int(callback.data.split(":")[1])

    if await update_dispatcher_status(disp_id, "rejected"):
        await callback.message.edit_text("❌ Диспетчер отклонен.")
    await callback.answer()