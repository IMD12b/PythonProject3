from sqlalchemy import func
from datetime import datetime, timedelta
from db.database import async_session, Courier, CourierShiftLog, Order, Dispatcher, DispatcherShiftLog
from sqlalchemy import select

# 1. СТАТИСТИКА ПО КУРЬЕРАМ ЗА ПЕРИОД
async def get_couriers_stats_for_period(date_from: datetime, date_to: datetime) -> list[dict]:
    async with async_session() as session:
        # Получаем всех активных курьеров
        couriers_res = await session.execute(select(Courier).where(Courier.status == "approved"))
        couriers = couriers_res.scalars().all()

        result = []
        for c in couriers:
            # Считаем часы
            logs_res = await session.execute(
                select(CourierShiftLog).where(
                    CourierShiftLog.courier_id == c.id,
                    CourierShiftLog.clock_in >= date_from,
                    CourierShiftLog.clock_in <= date_to
                )
            )
            logs = logs_res.scalars().all()
            total_hours = 0.0
            for log in logs:
                end = log.clock_out if log.clock_out else datetime.now()
                total_hours += (end - log.clock_in).total_seconds() / 3600

            # Считаем заказы
            orders_res = await session.execute(
                select(Order).where(
                    Order.courier_id == c.id,
                    Order.status == "✅ Доставлен",
                    Order.created_at >= date_from,
                    Order.created_at <= date_to
                )
            )
            delivered_count = len(orders_res.scalars().all())

            result.append({
                "name": c.name,
                "hours": round(total_hours, 1),
                "orders": delivered_count
            })
        return result


# 2. СТАТИСТИКА ПО ДИСПЕТЧЕРАМ ЗА ПЕРИОД
async def get_dispatchers_stats_for_period(date_from: datetime, date_to: datetime) -> list[dict]:
    async with async_session() as session:
        dispatchers_res = await session.execute(select(Dispatcher).where(Dispatcher.status == "approved"))
        dispatchers = dispatchers_res.scalars().all()

        result = []
        for d in dispatchers:
            logs_res = await session.execute(
                select(DispatcherShiftLog).where(
                    DispatcherShiftLog.dispatcher_id == d.id,
                    DispatcherShiftLog.clock_in >= date_from,
                    DispatcherShiftLog.clock_in <= date_to
                )
            )
            logs = logs_res.scalars().all()
            total_hours = 0.0
            for log in logs:
                end = log.clock_out if log.clock_out else datetime.now()
                total_hours += (end - log.clock_in).total_seconds() / 3600

            result.append({
                "name": d.name,
                "hours": round(total_hours, 1)
            })
        return result


# 3. СТАТИСТИКА ПО ЗАКАЗАМ ЗА ПЕРИОД
async def get_orders_stats_for_period(date_from: datetime, date_to: datetime) -> dict:
    async with async_session() as session:
        orders_res = await session.execute(
            select(Order).where(
                Order.created_at >= date_from,
                Order.created_at <= date_to
            )
        )
        orders = orders_res.scalars().all()

        delivered = len([o for o in orders if o.status == "✅ Доставлен"])
        cancelled = len([o for o in orders if "❌ Отменен" in o.status])
        # Недоставленные = те, что в ожидании или в пути
        undelivered = len([o for o in orders if o.status in ["🕒 Ожидает курьера", "🚚 В пути"]])

        return {
            "total": len(orders),
            "delivered": delivered,
            "undelivered": undelivered,
            "cancelled": cancelled
        }