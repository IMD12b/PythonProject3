# db/dispatcher_shifts.py
from datetime import datetime
from sqlalchemy import select

from db.database import async_session, DispatcherShift


async def add_dispatcher_shift(dispatcher_id: int, start: str, end: str) -> bool:
    async with async_session() as session:
        shift = DispatcherShift(dispatcher_id=dispatcher_id, start_time=start, end_time=end)
        session.add(shift)
        await session.commit()
        return True


async def get_dispatcher_shifts(dispatcher_id: int) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(DispatcherShift)
            .where(DispatcherShift.dispatcher_id == dispatcher_id)
            .order_by(DispatcherShift.start_time)
        )
        return [{"id": s.id, "start": s.start_time, "end": s.end_time} for s in result.scalars().all()]


async def is_dispatcher_on_shift(dispatcher_id: int) -> bool:
    shifts = await get_dispatcher_shifts(dispatcher_id)
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