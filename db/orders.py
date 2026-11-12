# db/orders.py
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.database import async_session, Courier, Order
from db.converters import order_to_dict


async def add_order(order_data: dict, dispatcher_id: int) -> int:
    async with async_session() as session:
        order = Order(
            address=order_data["address"],
            client_name=order_data["client_name"],
            client_phone=order_data["client_phone"],
            price=order_data["price"],
            status="🕒 Ожидает курьера",
            created_by_id=dispatcher_id
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
        return [order_to_dict(o) for o in result.scalars().all()]


async def get_order_by_id(order_id: int) -> dict | None:
    async with async_session() as session:
        result = await session.execute(
            select(Order).options(selectinload(Order.courier)).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        return order_to_dict(order) if order else None


async def get_available_orders() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.courier))
            .where(Order.status == "🕒 Ожидает курьера")
            .where(Order.courier_id.is_(None))
            .order_by(Order.id)
        )
        return [order_to_dict(o) for o in result.scalars().all()]


async def get_orders_by_courier(courier_id: int) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.courier))
            .where(Order.courier_id == courier_id)
            .order_by(Order.id)
        )
        return [order_to_dict(o) for o in result.scalars().all()]


async def assign_courier(order_id: int, courier_id: int) -> bool:
    async with async_session() as session:
        order_result = await session.execute(select(Order).where(Order.id == order_id))
        order = order_result.scalar_one_or_none()

        courier_result = await session.execute(select(Courier).where(Courier.id == courier_id))
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
        if not courier.is_on_shift:
            return False
        order.courier_id = courier.id
        order.status = "🚚 В пути"
        courier.is_busy = True
        await session.commit()
        return True


async def complete_order(order_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(Order).options(selectinload(Order.courier)).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            return False
        if order.courier is not None:
            order.courier.is_busy = False
        order.status = "✅ Доставлен"
        order.delivered_by_id = order.courier_id
        order.courier_id = None
        await session.commit()
        return True


async def cancel_order(order_id: int, reason: str = "Отменен") -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(Order).options(selectinload(Order.courier)).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            return False
        if order.courier is not None:
            order.courier.is_busy = False
        order.status = f"❌ Отменен ({reason})"
        order.courier_id = None
        await session.commit()
        return True