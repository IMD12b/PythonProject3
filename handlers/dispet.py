# handlers/dispet.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboard.dispt_key import admin_main_kb, order_cancel_kb, order_confirm_kb
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboard.dispt_key import admin_main_kb, order_cancel_kb, order_confirm_kb
from memory_db import add_order, get_all_orders, get_order_by_id, get_all_couriers, assign_courier

dispet_router = Router()


class OrderCreation(StatesGroup):
    waiting_address = State()
    waiting_client_name = State()
    waiting_client_phone = State()
    waiting_price = State()
    confirming = State()


@dispet_router.message(F.text == "➕ Создать заказ")
async def start_create_order(message: Message, state: FSMContext):
    await state.set_state(OrderCreation.waiting_address)
    await message.answer("Введите <b>адрес доставки</b>:", reply_markup=order_cancel_kb(), parse_mode="HTML")


@dispet_router.message(OrderCreation.waiting_address, F.text)
async def process_address(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено.", reply_markup=admin_main_kb())
    await state.update_data(address=message.text)
    await state.set_state(OrderCreation.waiting_client_name)
    await message.answer("Введите <b>имя клиента</b>:", parse_mode="HTML")


@dispet_router.message(OrderCreation.waiting_client_name, F.text)
async def process_client_name(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено.", reply_markup=admin_main_kb())
    await state.update_data(client_name=message.text)
    await state.set_state(OrderCreation.waiting_client_phone)
    await message.answer("Введите <b>телефон клиента</b>:", parse_mode="HTML")


@dispet_router.message(OrderCreation.waiting_client_phone, F.text)
async def process_client_phone(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено.", reply_markup=admin_main_kb())
    await state.update_data(client_phone=message.text)
    await state.set_state(OrderCreation.waiting_price)
    await message.answer("Введите <b>сумму заказа (в рублях)</b>:", parse_mode="HTML")


@dispet_router.message(OrderCreation.waiting_price, F.text)
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
    await state.set_state(OrderCreation.confirming)
    await message.answer(confirm_text, reply_markup=order_confirm_kb(), parse_mode="HTML")


@dispet_router.message(OrderCreation.confirming, F.text == "✅ Сохранить")
async def save_order_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    # СОХРАНЯЕМ В ПАМЯТЬ!
    order_id = add_order(data)

    await state.clear()
    await message.answer(
        f"✅ Заказ <b>#{order_id}</b> успешно создан!",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )


@dispet_router.message(OrderCreation.confirming, F.text == "❌ Отмена")
async def cancel_confirmation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Создание заказа отменено.", reply_markup=admin_main_kb())


# --- КНОПКА "ВСЕ ЗАКАЗЫ" ---
@dispet_router.message(F.text == "📊 Все заказы")
async def show_all_orders(message: Message):
    orders = get_all_orders()

    if not orders:
        return await message.answer("Пока нет созданных заказов.")

    for order in orders:
        # Формируем текст для одного заказа
        text = (
            f"<b>Заказ #{order['id']}</b> ({order['status']})\n"
            f"📍 {order['address']}\n"
            f"👤 {order['client_name']} | 📞 {order['client_phone']}\n"
            f"💰 {order['price']} ₽\n"
        )

        if order['courier_name']:
            text += f"🛵 Курьер: {order['courier_name']}"

            # Если курьер уже назначен, кнопку не показываем
            await message.answer(text, parse_mode="HTML")
        else:
            # Если курьера нет — показываем кнопку
            builder = InlineKeyboardBuilder()
            builder.button(
                text="👤 Назначить курьера",
                callback_data=f"assign_menu:{order['id']}"
            )
            await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


# --- ВЫБОР КУРЬЕРА ДЛЯ ЗАКАЗА ---
@dispet_router.callback_query(F.data.startswith("assign_menu:"))
async def show_couriers_for_order(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    couriers = get_all_couriers()

    builder = InlineKeyboardBuilder()
    for courier in couriers:
        builder.button(
            text=courier["name"],
            callback_data=f"do_assign:{order_id}:{courier['id']}"
        )
    builder.adjust(1)  # По одной кнопке в ряд

    await callback.message.edit_text(
        f"Выберите курьера для заказа <b>#{order_id}</b>:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


# --- САМО НАЗНАЧЕНИЕ ---
@dispet_router.callback_query(F.data.startswith("do_assign:"))
async def process_assignment(callback: CallbackQuery):
    # Достаем ID заказа и ID курьера из callback_data
    _, order_id_str, courier_id_str = callback.data.split(":")
    order_id = int(order_id_str)
    courier_id = int(courier_id_str)

    success = assign_courier(order_id, courier_id)

    if success:
        order = get_order_by_id(order_id)
        await callback.message.edit_text(
            f"✅ Заказ <b>#{order_id}</b> назначен на курьера <b>{order['courier_name']}</b>.",
            parse_mode="HTML"
        )
        await callback.answer("Курьер назначен!")
    else:
        await callback.answer("Ошибка при назначении", show_alert=True)