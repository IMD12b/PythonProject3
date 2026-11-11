# handlers/dispatcher/__init__.py
from handlers.dispatcher.orders import dispatcher_orders_router
from handlers.dispatcher.couriers import dispatcher_couriers_router
from handlers.dispatcher.shifts import dispatcher_shifts_router

__all__ = [
    "dispatcher_orders_router",
    "dispatcher_couriers_router",
    "dispatcher_shifts_router",
]