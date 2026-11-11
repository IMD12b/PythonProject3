# db/courier_shifts.py
from datetime import datetime
from sqlalchemy import select

from db.database import async_session, Shift


async def add_shift(courier_id: int, start: str, end: str) -> bool:
    async with async_session() as session:
        shift = Shift(courier_id=courier_id, start_time=start, end_time=end)
        session.add(shift)
        await session.commit()
        return True


async def get_courier_shifts(courier_id: int) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Shift).where(Shift.courier_id == courier_id).order_by(Shift.start_time)
        )
        return [
            {"id": s.id, "start": s.start_time, "end": s.end_time}
            for s in result.scalars().all()
        ]


async def is_courier_on_shift(courier_id: int) -> bool:
    shifts = await get_courier_shifts(courier_id)
    now = datetime.now()
    for shift in shifts:
        try:
            start_time = datetime.strptime(shift["start"], "%Y-%m-%d %H:%M")
            end_time = datetime.strptime(shift["end"], "%Y-%m-%d %H:%M")
            if start_time <= now <= end_time:
                return True
        except ValueError:
            continue
    return False