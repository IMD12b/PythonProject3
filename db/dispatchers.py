# db/dispatchers.py
from sqlalchemy import select

from db.database import async_session, Dispatcher
from db.converters import dispatcher_to_dict


async def get_all_dispatchers() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(select(Dispatcher).order_by(Dispatcher.id))
        return [dispatcher_to_dict(d) for d in result.scalars().all()]


async def get_dispatcher_by_id(dispatcher_id: int) -> dict | None:
    async with async_session() as session:
        result = await session.execute(select(Dispatcher).where(Dispatcher.id == dispatcher_id))
        dispatcher = result.scalar_one_or_none()
        return dispatcher_to_dict(dispatcher) if dispatcher else None


async def get_dispatcher_by_tg_id(tg_id: int) -> dict | None:
    async with async_session() as session:
        print(f"--- DEBUG: Ищу диспетчера с ID: {tg_id}")  # <--- Отладка

        result = await session.execute(select(Dispatcher).where(Dispatcher.telegram_id == tg_id))
        dispatcher = result.scalar_one_or_none()

        if dispatcher:
            print(f"--- DEBUG: Найден! {dispatcher.name}")  # <--- Отладка
        else:
            print("--- DEBUG: НЕ НАЙДЕН!")  # <--- Отладка

        return dispatcher_to_dict(dispatcher) if dispatcher else None


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
        if not dispatcher:
            return False
        dispatcher.status = new_status
        await session.commit()
        return True


async def toggle_dispatcher_shift_status(dispatcher_id: int, status: bool) -> bool:
    async with async_session() as session:
        result = await session.execute(select(Dispatcher).where(Dispatcher.id == dispatcher_id))
        disp = result.scalar_one_or_none()
        if not disp:
            return False
        disp.is_on_shift = status
        await session.commit()
        return True