# db/couriers.py
from sqlalchemy import select

from db.database import async_session, Courier
from db.converters import courier_to_dict


async def get_all_couriers() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(select(Courier).order_by(Courier.id))
        return [courier_to_dict(c) for c in result.scalars().all()]


async def get_courier_by_id(courier_id: int) -> dict | None:
    async with async_session() as session:
        result = await session.execute(select(Courier).where(Courier.id == courier_id))
        courier = result.scalar_one_or_none()
        return courier_to_dict(courier) if courier else None


async def get_courier_by_tg_id(tg_id: int) -> dict | None:
    async with async_session() as session:
        result = await session.execute(select(Courier).where(Courier.telegram_id == tg_id))
        courier = result.scalar_one_or_none()
        if courier:
            print(f"--- DEBUG: НайдеХуйн! {courier.name}")  # <--- Отладка
        else:
            print("--- DEBUG: НЕ НАЙДЕХуйН!")  # <--- Отладка

        return courier_to_dict(courier) if courier else None


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
        result = await session.execute(select(Courier).where(Courier.id == courier_id))
        courier = result.scalar_one_or_none()
        if not courier:
            return False
        courier.status = new_status
        await session.commit()
        return True


async def toggle_courier_shift_status(courier_id: int, status: bool) -> bool:
    async with async_session() as session:
        result = await session.execute(select(Courier).where(Courier.id == courier_id))
        courier = result.scalar_one_or_none()
        if not courier:
            return False
        courier.is_on_shift = status
        await session.commit()
        return True


async def get_free_approved_couriers() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Courier)
            .where(Courier.status == "approved")
            .where(Courier.is_busy.is_(False))
            .where(Courier.is_on_shift.is_(True))
            .order_by(Courier.id)
        )
        return [courier_to_dict(c) for c in result.scalars().all()]