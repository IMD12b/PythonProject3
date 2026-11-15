# db/courier_shift.py
from datetime import datetime
from sqlalchemy import select

from db.database import async_session, Shift, CourierShiftLog


# ---------- ГРАФИК (назначает модератор) ----------

async def add_shift(courier_id: int, start: str, end: str) -> int:
    async with async_session() as session:
        shift = Shift(courier_id=courier_id, start_time=start, end_time=end)
        session.add(shift)
        await session.commit()
        await session.refresh(shift)
        return shift.id


async def get_courier_shifts(courier_id: int) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Shift).where(Shift.courier_id == courier_id).order_by(Shift.start_time)
        )
        return [
            {"id": s.id, "start": s.start_time, "end": s.end_time}
            for s in result.scalars().all()
        ]


async def get_shift_by_id(shift_id: int) -> dict | None:
    async with async_session() as session:
        result = await session.execute(select(Shift).where(Shift.id == shift_id))
        s = result.scalar_one_or_none()
        return {
            "id": s.id,
            "courier_id": s.courier_id,
            "start": s.start_time,
            "end": s.end_time,
        } if s else None


async def update_shift(shift_id: int, start: str, end: str) -> bool:
    async with async_session() as session:
        result = await session.execute(select(Shift).where(Shift.id == shift_id))
        s = result.scalar_one_or_none()
        if not s:
            return False
        s.start_time = start
        s.end_time = end
        await session.commit()
        return True


async def delete_shift(shift_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(select(Shift).where(Shift.id == shift_id))
        s = result.scalar_one_or_none()
        if not s:
            return False
        await session.delete(s)
        await session.commit()
        return True


async def is_courier_on_shift(courier_id: int) -> bool:
    """Проверяет, попадает ли текущее время в график."""
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


# ---------- ЛОГИ (фактическое начало/конец смены) ----------

async def start_courier_shift_log(courier_id: int) -> int:
    """Создаёт запись о начале смены. Возвращает id лога."""
    async with async_session() as session:
        log = CourierShiftLog(courier_id=courier_id, clock_in=datetime.now())
        session.add(log)
        await session.commit()
        await session.refresh(log)
        return log.id


async def end_courier_shift_log(courier_id: int) -> bool:
    """Закрывает последнюю открытую смену (clock_out = now)."""
    async with async_session() as session:
        result = await session.execute(
            select(CourierShiftLog)
            .where(CourierShiftLog.courier_id == courier_id)
            .where(CourierShiftLog.clock_out.is_(None))
            .order_by(CourierShiftLog.clock_in.desc())
        )
        log = result.scalars().first()
        if not log:
            return False
        log.clock_out = datetime.now()
        await session.commit()
        return True


async def get_courier_shift_logs(courier_id: int, limit: int = 20) -> list[dict]:
    """История фактических смен курьера (для отчётов/модератора)."""
    async with async_session() as session:
        result = await session.execute(
            select(CourierShiftLog)
            .where(CourierShiftLog.courier_id == courier_id)
            .order_by(CourierShiftLog.clock_in.desc())
            .limit(limit)
        )
        return [
            {
                "id": log.id,
                "clock_in": log.clock_in,
                "clock_out": log.clock_out,
            }
            for log in result.scalars().all()
        ]