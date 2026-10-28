# memory_db.py
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.database import async_session, Courier, Order


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
            select(Order).options(selectinload(Order.courier)).order_by(Order.id)
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