# db/enterprises.py
from sqlalchemy import select

from db.database import async_session, Enterprise


async def add_enterprise(name: str, address: str, lat: float, lon: float) -> int:
    async with async_session() as session:
        ent = Enterprise(name=name, address=address, lat=lat, lon=lon)
        session.add(ent)
        await session.commit()
        await session.refresh(ent)
        return ent.id


async def get_all_enterprises() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(select(Enterprise).order_by(Enterprise.id))
        return [
            {"id": e.id, "name": e.name, "address": e.address, "lat": e.lat, "lon": e.lon}
            for e in result.scalars().all()
        ]


async def get_enterprise_by_id(ent_id: int) -> dict | None:
    async with async_session() as session:
        result = await session.execute(select(Enterprise).where(Enterprise.id == ent_id))
        e = result.scalar_one_or_none()
        return (
            {"id": e.id, "name": e.name, "address": e.address, "lat": e.lat, "lon": e.lon}
            if e else None
        )