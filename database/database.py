# database.py
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String
from typing import Optional

from config import DATABASE_URL


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass




class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(primary_key=True)
    courier_id: Mapped[int] = mapped_column(ForeignKey("couriers.id", ondelete="CASCADE"))
    # Храним как строки, чтобы не возиться с часовыми поясами в БД
    start_time: Mapped[str] = mapped_column(String(30))
    end_time: Mapped[str] = mapped_column(String(30))

    courier: Mapped["Courier"] = relationship(back_populates="shifts")

class Courier(Base):
    __tablename__ = "couriers"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    is_busy: Mapped[bool] = mapped_column(default=False)

    orders: Mapped[list["Order"]] = relationship(back_populates="courier")

    shifts: Mapped[list["Shift"]] = relationship(back_populates="courier", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String(255))
    client_name: Mapped[str] = mapped_column(String(100))
    client_phone: Mapped[str] = mapped_column(String(30))
    price: Mapped[int]
    status: Mapped[str] = mapped_column(String(50), default="Ожидает курьера")

    courier_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("couriers.id", ondelete="SET NULL"),
        nullable=True,
    )
    courier: Mapped[Optional["Courier"]] = relationship(back_populates="orders")

class Dispatcher(Base):
    __tablename__ = "dispatchers"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="pending") # pending / approved / rejected

    shifts: Mapped[list["DispatcherShift"]] = relationship(back_populates="dispatcher", cascade="all, delete-orphan")

class DispatcherShift(Base):
    __tablename__ = "dispatcher_shifts"

    id: Mapped[int] = mapped_column(primary_key=True)
    dispatcher_id: Mapped[int] = mapped_column(ForeignKey("dispatchers.id", ondelete="CASCADE"))
    start_time: Mapped[str] = mapped_column(String(30))
    end_time: Mapped[str] = mapped_column(String(30))

    dispatcher: Mapped["Dispatcher"] = relationship(back_populates="shifts")


async def init_db() -> None:
    """Создаёт таблицы, если их нет. Вызвать один раз при старте."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)