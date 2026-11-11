# memory_db.py
from db.orders import (
    add_order, get_all_orders, get_order_by_id,
    get_available_orders, get_orders_by_courier,
    assign_courier, complete_order, cancel_order,
)
from db.couriers import (
    register_courier, get_all_couriers, get_courier_by_id,
    get_courier_by_tg_id, update_courier_status,
    toggle_courier_shift_status, get_free_approved_couriers,
)
from db.courier_shift import add_shift, get_courier_shifts, is_courier_on_shift
from db.dispatchers import (
    register_dispatcher, get_all_dispatchers, get_dispatcher_by_id,
    get_dispatcher_by_tg_id, update_dispatcher_status,
    toggle_dispatcher_shift_status,
)
from db.dispatcher_shifts import (
    add_dispatcher_shift, get_dispatcher_shifts, is_dispatcher_on_shift,
)

__all__ = [
    # orders
    "add_order", "get_all_orders", "get_order_by_id",
    "get_available_orders", "get_orders_by_courier",
    "assign_courier", "complete_order", "cancel_order",
    # couriers
    "register_courier", "get_all_couriers", "get_courier_by_id",
    "get_courier_by_tg_id", "update_courier_status",
    "toggle_courier_shift_status", "get_free_approved_couriers",
    # courier shifts
    "add_shift", "get_courier_shifts", "is_courier_on_shift",
    # dispatchers
    "register_dispatcher", "get_all_dispatchers", "get_dispatcher_by_id",
    "get_dispatcher_by_tg_id", "update_dispatcher_status",
    "toggle_dispatcher_shift_status",
    # dispatcher shifts
    "add_dispatcher_shift", "get_dispatcher_shifts", "is_dispatcher_on_shift",
]