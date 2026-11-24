# db/orders.py
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from db.database import async_session, Courier, Order
from db.converters import order_to_dict
from db.ml_assign import calculate_knn_distribution


async def add_order(order_data: dict, dispatcher_id: int) -> int:
    async with async_session() as session:
        order = Order(
            address=order_data["address"],
            client_name=order_data["client_name"],
            client_phone=order_data["client_phone"],
            price=order_data["price"],
            lat=order_data.get("lat"),  # <--- ДОБАВИЛИ
            lon=order_data.get("lon"),
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


async def auto_assign_knn() -> int:
    async with async_session() as session:
        # 1. Получаем заказы с координатами
        orders_res = await session.execute(
            select(Order).where(
                Order.status == "🕒 Ожидает курьера",
                Order.lat.is_not(None),
                Order.lon.is_not(None)
            ).order_by(Order.created_at)
        )
        orders = orders_res.scalars().all()

        # 2. Получаем курьеров
        couriers_res = await session.execute(
            select(Courier).where(
                Courier.status == "approved",
                Courier.is_on_shift == True
            )
        )
        couriers = couriers_res.scalars().all()

        if not orders or not couriers:
            return 0

        # 3. Считаем текущую загрузку курьеров (сколько заказов В ПУТИ)
        courier_loads = {}
        for c in couriers:
            count_res = await session.execute(
                select(func.count(Order.id)).where(
                    Order.courier_id == c.id,
                    Order.status == "🚚 В пути"
                )
            )
            courier_loads[c.id] = count_res.scalar()

        # 4. Готовим данные для ML-функции (превращаем объекты БД в словари)
        orders_data = [{"id": o.id, "lat": o.lat, "lon": o.lon} for o in orders]
        couriers_data = [{"id": c.id, "max_orders": c.max_orders} for c in couriers]

        # 5. Вызываем "мозг" (KNN)
        distribution = calculate_knn_distribution(orders_data, couriers_data, courier_loads)

        # 6. Сохраняем результат в БД
        assigned_count = len(distribution)
        if assigned_count > 0:
            for order_id, courier_id in distribution.items():
                # Обновляем заказ
                await session.execute(
                    Order.__table__.update().where(Order.id == order_id).values(
                        courier_id=courier_id,
                        status="🚚 В пути"
                    )
                )
            await session.commit()

        return assigned_count