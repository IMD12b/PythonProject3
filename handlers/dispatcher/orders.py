import asyncio

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.couriers import get_free_approved_couriers
from db.geocoder import get_coordinates
from db.dispatchers import get_dispatcher_by_tg_id
from db.orders import auto_assign_loop
from keyboard.dispt_key import admin_main_kb, order_cancel_kb, order_confirm_kb
from keyboard.courer_key import courier_main_kb
from db.memory_db import (
    add_order, get_all_orders, get_order_by_id,
    get_all_couriers, get_courier_by_id, assign_courier,
)
from db.enterprises import get_all_enterprises, get_enterprise_by_id


dispatcher_orders_router = Router()

class OrderCreation(StatesGroup):
    waiting_enterprise = State()  # выбор предприятия
    waiting_address = State()  # адрес клиента
    waiting_client_name = State()
    waiting_client_phone = State()
    waiting_price = State()
    confirming = State()

@dispatcher_orders_router.message(F.text == "➕ Создать заказ")
async def start_create_order(message: Message, state: FSMContext):
    disp = await get_dispatcher_by_tg_id(message.from_user.id)
    if not disp:
        return await message.answer("Тебя нет в базе.")

    if not disp["is_on_shift"]:
        return await message.answer("⛔ Ты не на смене! Нажми «Начать/Закончить смену», чтобы начать работу.")

    enterprises = await get_all_enterprises()
    if not enterprises:
        return await message.answer("🏭 Предприятий пока нет. Обратитесь к модератору.")

    builder = InlineKeyboardBuilder()
    for e in enterprises:
        builder.button(text=e["name"], callback_data=f"pick_ent:{e['id']}")
    builder.adjust(1)

    await state.set_state(OrderCreation.waiting_enterprise)        # ← ждём выбора предприятия
    await message.answer(
        "Выберите <b>предприятие</b>, откуда курьер заберёт заказ:",
        reply_markup=builder.as_markup(),                          # ← прикрепляем клавиатуру
        parse_mode="HTML",
    )
@dispatcher_orders_router.callback_query(
    OrderCreation.waiting_enterprise,
    F.data.startswith("pick_ent:"),
)
async def pick_enterprise(callback: CallbackQuery, state: FSMContext):
    ent_id = int(callback.data.split(":")[1])
    ent = await get_enterprise_by_id(ent_id)
    if not ent:
        return await callback.answer("Предприятие не найдено", show_alert=True)

    await state.update_data(enterprise_id=ent_id)                  # ← ключевая строка
    await state.set_state(OrderCreation.waiting_address)

    await callback.message.edit_text(
        f"🏭 Предприятие: <b>{ent['name']}</b>\n"
        f"📍 {ent['address']}\n\n"
        f"Введите <b>адрес доставки</b>:",
        parse_mode="HTML",
    )
    await callback.answer()

@dispatcher_orders_router.message(OrderCreation.waiting_address, F.text)
async def process_address(message: Message, state: FSMContext):
    address_text = message.text
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено.", reply_markup=admin_main_kb())

    coords = get_coordinates(address_text)

    if coords:
        lat, lon = coords
        await state.update_data(address=address_text, lat=lat, lon=lon)
        await state.set_state(OrderCreation.waiting_client_name)
        await message.answer(f"✅ Адрес найден на карте (Координаты: {lat:.4f}, {lon:.4f}).\nВведите имя клиента:")
    else:
        # Если адрес не найден, просим ввести заново (или можно сохранить без координат)
        await message.answer(
            "❌ Не удалось найти этот адрес на карте. Попробуйте ввести более точный адрес (например, 'город, улица, дом').")


@dispatcher_orders_router.message(OrderCreation.waiting_client_name, F.text)
async def process_client_name(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено.", reply_markup=admin_main_kb())
    await state.update_data(client_name=message.text)
    await state.set_state(OrderCreation.waiting_client_phone)
    await message.answer("Введите <b>телефон клиента</b>:", parse_mode="HTML")


@dispatcher_orders_router.message(OrderCreation.waiting_client_phone, F.text)
async def process_client_phone(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено.", reply_markup=admin_main_kb())
    await state.update_data(client_phone=message.text)
    await state.set_state(OrderCreation.waiting_price)
    await message.answer("Введите <b>сумму заказа (в рублях)</b>:", parse_mode="HTML")


@dispatcher_orders_router.message(OrderCreation.waiting_price, F.text)
async def process_price(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено.", reply_markup=admin_main_kb())

    if not message.text.isdigit():
        return await message.answer("Пожалуйста, введите число (например, 500).")

    await state.update_data(price=int(message.text))
    data = await state.get_data()

    confirm_text = (
        f"<b>Проверьте данные заказа:</b>\n\n"
        f"📍 Адрес: {data['address']}\n"
        f"👤 Клиент: {data['client_name']}\n"
        f"📞 Телефон: {data['client_phone']}\n"
        f"💰 Сумма: {data['price']} ₽\n\n"
        f"Все верно?"
    )
    await state.update_data(price=int(message.text))


    await state.set_state(OrderCreation.confirming)
    await message.answer(confirm_text, reply_markup=order_confirm_kb(), parse_mode="HTML")



@dispatcher_orders_router.message(OrderCreation.confirming, F.text == "✅ Сохранить")
async def save_order_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    disp = await get_dispatcher_by_tg_id(message.from_user.id)
    order_id = await add_order(data, disp["id"])                 # ← await

    await state.clear()
    await message.answer(
        f"✅ Заказ <b>#{order_id}</b> успешно создан!",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )


@dispatcher_orders_router.message(OrderCreation.confirming, F.text == "❌ Отмена")
async def cancel_confirmation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Создание заказа отменено.", reply_markup=admin_main_kb())


@dispatcher_orders_router.message(F.text == "📊 Все заказы")
async def show_all_orders(message: Message):
    orders = await get_all_orders()                  # ← await
    disp = await get_dispatcher_by_tg_id(message.from_user.id)
    if not disp:
        return await message.answer("Тебя нет в базе.")

    if not disp["is_on_shift"]:
        return await message.answer("⛔ Ты не на смене! Нажми «Начать/Закончить смену», чтобы начать работу.")

    if not orders:
        return await message.answer("Пока нет созданных заказов.")

    for order in orders:
        text = (
            f"<b>Заказ #{order['id']}</b> ({order['status']})\n"
            f"📍 {order['address']}\n"
            f"👤 {order['client_name']} | 📞 {order['client_phone']}\n"
            f"💰 {order['price']} ₽\n"
        )

        if order['courier_name']:
            text += f"🛵 Курьер: {order['courier_name']}"

        # Кнопку показываем ТОЛЬКО если заказ реально можно назначить
        if order['status'] == "🕒 Ожидает курьера" and order['courier_name'] is None:
            builder = InlineKeyboardBuilder()
            builder.button(
                text="👤 Назначить курьера",
                callback_data=f"assign_menu:{order['id']}"
            )
            await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(text, parse_mode="HTML")


@dispatcher_orders_router.callback_query(F.data.startswith("assign_menu:"))
async def show_couriers_for_order(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])

    order = await get_order_by_id(order_id)
    if not order:
        return await callback.answer("Заказ не найден", show_alert=True)
    if order["status"] != "🕒 Ожидает курьера" or order["courier_name"] is not None:
        return await callback.answer(
            f"Заказ уже нельзя назначить (статус: {order['status']})",
            show_alert=True
        )

    couriers = await get_free_approved_couriers()              # ← await
    if not couriers:
        return await callback.answer(
            "Нет свободных курьеров на смене. ",
            show_alert=True
        )
    builder = InlineKeyboardBuilder()
    for courier in couriers:
        builder.button(
            text=courier["name"],
            callback_data=f"do_assign:{order_id}:{courier['id']}"
        )
    builder.adjust(1)

    await callback.message.edit_text(
        f"Выберите курьера для заказа <b>#{order_id}</b>:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@dispatcher_orders_router.callback_query(F.data.startswith("do_assign:"))
async def process_assignment(callback: CallbackQuery, bot: Bot):
    _, order_id_str, courier_id_str = callback.data.split(":")
    order_id = int(order_id_str)
    courier_id = int(courier_id_str)

    success = await assign_courier(order_id, courier_id)

    if not success:
        await callback.answer("Ошибка при назначении", show_alert=True)
        return

    order = await get_order_by_id(order_id)
    courier = await get_courier_by_id(courier_id)          # ← по правильному ID

    await callback.message.edit_text(
        f"✅ Заказ <b>#{order_id}</b> назначен на курьера <b>{order['courier_name']}</b>.",
        parse_mode="HTML"
    )
    await callback.answer("Курьер назначен!")

    if courier is None:                                     # ← защита от None
        await callback.message.answer(
            "⚠️ Курьер не найден в базе, уведомление не отправлено."
        )
        return

    try:
        await bot.send_message(
            chat_id=courier["telegram_id"],
            text="Тебе назначен новый заказ!",
            reply_markup=courier_main_kb()
        )
    except Exception as e:
        await callback.message.answer(f"⚠️ Не удалось уведомить курьера о заказе: {e}")


@dispatcher_orders_router.message(F.text == "🧠 Автоназначение")
async def auto_assign_handler(message: Message, bot: Bot):
    # Проверяем диспетчера
    disp = await get_dispatcher_by_tg_id(message.from_user.id)
    if not disp or not disp["is_on_shift"]:
        return await message.answer("⛔ Ты не на смене!")

    # Отправляем мгновенный ответ
    await message.answer(
        "🚀 <b>Фоновое автоназначение запущено!</b>\n\n"
        "Бот будет распределять заказы по мере их поступления. "
        "Как только он закончит (или заказы кончатся), я пришлю тебе отчет.",
        parse_mode="HTML"
    )

    # ЗАПУСКАЕМ В ФОНЕ (не блокирует бота)
    asyncio.create_task(auto_assign_loop(bot))
