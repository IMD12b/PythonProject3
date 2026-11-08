# memory_db.py
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from database.database import async_session, Courier, Order, Shift, Dispatcher, DispatcherShift


# ---------- ORM → dict ----------

def _order_to_dict(order: Order) -> dict:
    return {
        "id": order.id,
        "address": order.address,
        "client_name": order.client_name,
        "client_phone": order.client_phone,
        "price": order.price,
        "status": order.status,
        "courier_name": order.courier.name if order.courier else None,
    }


def _courier_to_dict(courier: Courier) -> dict:
    return {
        "id": courier.id,
        "telegram_id": courier.telegram_id,
        "name": courier.name,
        "phone": courier.phone,
        "status": courier.status,
        "is_busy": courier.is_busy,
    }


# ---------- ЗАКАЗЫ (исходные) ----------

async def add_order(order_data: dict) -> int:
    async with async_session() as session:
        order = Order(
            address=order_data["address"],
            client_name=order_data["client_name"],
            client_phone=order_data["client_phone"],
            price=order_data["price"],
            status="🕒 Ожидает курьера",
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order.id


async def get_all_orders() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Order).options(selectinload(Order.courier)).
            order_by(Order.id)
        )
        return [_order_to_dict(o) for o in result.scalars().all()]


async def get_order_by_id(order_id: int) -> dict | None:
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.courier))
            .where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        return _order_to_dict(order) if order else None


# ---------- КУРЬЕРЫ (исходные) ----------

async def get_all_couriers() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(select(Courier).order_by(Courier.id))
        return [_courier_to_dict(c) for c in result.scalars().all()]


async def get_courier_by_id(courier_id: int) -> dict | None:
    async with async_session() as session:
        result = await session.execute(
            select(Courier).where(Courier.id == courier_id)
        )
        courier = result.scalar_one_or_none()
        return _courier_to_dict(courier) if courier else None


async def get_courier_by_tg_id(tg_id: int) -> dict | None:
    async with async_session() as session:
        result = await session.execute(
            select(Courier).where(Courier.telegram_id == tg_id)
        )
        courier = result.scalar_one_or_none()
        return _courier_to_dict(courier) if courier else None


async def register_courier(tg_id: int, name: str, phone: str) -> int:
    async with async_session() as session:
        courier = Courier(
            telegram_id=tg_id,
            name=name,
            phone=phone,
            status="pending",
            is_busy=False,
        )
        session.add(courier)
        await session.commit()
        await session.refresh(courier)
        return courier.id


async def update_courier_status(courier_id: int, new_status: str) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(Courier).where(Courier.id == courier_id)
        )
        courier = result.scalar_one_or_none()
        if not courier:
            return False
        courier.status = new_status
        await session.commit()
        return True


# ---------- НАЗНАЧЕНИЕ (исходная, усиленная) ----------

async def assign_courier(order_id: int, courier_id: int) -> bool:
    async with async_session() as session:
        order_result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = order_result.scalar_one_or_none()

        courier_result = await session.execute(
            select(Courier).where(Courier.id == courier_id)
        )
        courier = courier_result.scalar_one_or_none()

        if not order or not courier:
            return False
        if courier.status != "approved":
            return False
        if courier.is_busy:
            return False
        if order.courier_id is not None:
            return False
        if order.status != "🕒 Ожидает курьера":
            return False
        order.courier_id = courier.id
        order.status = "🚚 В пути"
        courier.is_busy = True
        await session.commit()
        return True


# =========================================================
# НОВЫЕ ФУНКЦИИ
# =========================================================

# ---------- Для курьера ----------

async def get_available_orders() -> list[dict]:
    """Свободные заказы: статус «Ожидает курьера», courier_id = NULL."""
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.courier))
            .where(Order.status == "🕒 Ожидает курьера")
            .where(Order.courier_id.is_(None))
            .order_by(Order.id)
        )
        return [_order_to_dict(o) for o in result.scalars().all()]


async def get_orders_by_courier(courier_id: int) -> list[dict]:
    """Все заказы, привязанные к курьеру (для «Мой заказ»)."""
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.courier))
            .where(Order.courier_id == courier_id)
            .order_by(Order.id)
        )
        return [_order_to_dict(o) for o in result.scalars().all()]


async def complete_order(order_id: int) -> bool:
    """Завершает заказ и освобождает курьера (is_busy = False)."""
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.courier))
            .where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            return False
        if order.courier is not None:
            order.courier.is_busy = False
        order.status = "✅ Доставлен"
        order.courier_id = None
        await session.commit()
        return True


# ---------- Для диспетчера ----------

async def get_free_approved_couriers() -> list[dict]:
    """Курьеры, которых можно назначить: approved и не заняты."""
    async with async_session() as session:
        result = await session.execute(
            select(Courier)
            .where(Courier.status == "approved")
            .where(Courier.is_busy.is_(False))
            .order_by(Courier.id)
        )
        return [_courier_to_dict(c) for c in result.scalars().all()]


async def add_shift(courier_id: int, start: str, end: str) -> bool:
    """Добавляет новую смену курьеру"""
    async with async_session() as session:
        shift = Shift(courier_id=courier_id, start_time=start, end_time=end)
        session.add(shift)
        await session.commit()
        return True


async def get_courier_shifts(courier_id: int) -> list[dict]:
    """Возвращает все смены конкретного курьера"""
    async with async_session() as session:
        result = await session.execute(
            select(Shift)
            .where(Shift.courier_id == courier_id)
            .order_by(Shift.start_time)
        )
        return [
            {"id": s.id, "start": s.start_time, "end": s.end_time}
            for s in result.scalars().all()
        ]


async def is_courier_on_shift(courier_id: int) -> bool:
    """Проверяет, есть ли у курьера АКТИВНАЯ смена прямо сейчас"""
    shifts = await get_courier_shifts(courier_id)
    now = datetime.now()

    for shift in shifts:
        try:
            start_time = datetime.strptime(shift["start"], "%Y-%m-%d %H:%M")
            end_time = datetime.strptime(shift["end"], "%Y-%m-%d %H:%M")
            if start_time <= now <= end_time:
                return True
        except ValueError:
            continue  # Если формат битый, пропускаем эту смену

    return False

# ==========================================
# ФУНКЦИИ ДЛЯ ДИСПЕТЧЕРОВ
# ==========================================

def _dispatcher_to_dict(dispatcher: Dispatcher) -> dict:
    return {
        "id": dispatcher.id,
        "telegram_id": dispatcher.telegram_id,
        "name": dispatcher.name,
        "phone": dispatcher.phone,
        "status": dispatcher.status,
    }

async def get_all_dispatchers() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(select(Dispatcher).order_by(Dispatcher.id))
        return [_dispatcher_to_dict(d) for d in result.scalars().all()]

async def get_dispatcher_by_id(dispatcher_id: int) -> dict | None:
    async with async_session() as session:
        result = await session.execute(select(Dispatcher).where(Dispatcher.id == dispatcher_id))
        dispatcher = result.scalar_one_or_none()
        return _dispatcher_to_dict(dispatcher) if dispatcher else None

async def get_dispatcher_by_tg_id(tg_id: int) -> dict | None:
    async with async_session() as session:
        result = await session.execute(select(Dispatcher).where(Dispatcher.telegram_id == tg_id))
        dispatcher = result.scalar_one_or_none()
        return _dispatcher_to_dict(dispatcher) if dispatcher else None

async def register_dispatcher(tg_id: int, name: str, phone: str) -> int:
    async with async_session() as session:
        dispatcher = Dispatcher(telegram_id=tg_id, name=name, phone=phone, status="pending")
        session.add(dispatcher)
        await session.commit()
        await session.refresh(dispatcher)
        return dispatcher.id

async def update_dispatcher_status(dispatcher_id: int, new_status: str) -> bool:
    async with async_session() as session:
        result = await session.execute(select(Dispatcher).where(Dispatcher.id == dispatcher_id))
        dispatcher = result.scalar_one_or_none()
        if not dispatcher: return False
        dispatcher.status = new_status
        await session.commit()
        return True

async def add_dispatcher_shift(dispatcher_id: int, start: str, end: str) -> bool:
    async with async_session() as session:
        shift = DispatcherShift(dispatcher_id=dispatcher_id, start_time=start, end_time=end)
        session.add(shift)
        await session.commit()
        return True

async def get_dispatcher_shifts(dispatcher_id: int) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(select(DispatcherShift).where(DispatcherShift.dispatcher_id == dispatcher_id).order_by(DispatcherShift.start_time))
        return [{"id": s.id, "start": s.start_time, "end": s.end_time} for s in result.scalars().all()]

async def is_dispatcher_on_shift(dispatcher_id: int) -> bool:
    shifts = await get_dispatcher_shifts(dispatcher_id)
    now = datetime.now()
    for shift in shifts:
        try:
            start_time = datetime.strptime(shift["start"], "%Y-%m-%d %H:%M")
            end_time = datetime.strptime(shift["end"], "%Y-%m-%d %H:%M")
            if start_time <= now <= end_time: return True
        except ValueError: continue
    return False