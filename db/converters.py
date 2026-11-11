# db/converters.py
from db.database import Courier, Order, Dispatcher


def order_to_dict(order: Order) -> dict:
    return {
        "id": order.id,
        "address": order.address,
        "client_name": order.client_name,
        "client_phone": order.client_phone,
        "price": order.price,
        "status": order.status,
        "courier_name": order.courier.name if order.courier else None,
    }


def courier_to_dict(courier: Courier) -> dict:
    return {
        "id": courier.id,
        "telegram_id": courier.telegram_id,
        "name": courier.name,
        "phone": courier.phone,
        "status": courier.status,
        "is_busy": courier.is_busy,
        "is_on_shift": courier.is_on_shift,
    }


def dispatcher_to_dict(dispatcher: Dispatcher) -> dict:
    return {
        "id": dispatcher.id,
        "telegram_id": dispatcher.telegram_id,
        "name": dispatcher.name,
        "phone": dispatcher.phone,
        "status": dispatcher.status,
        "is_on_shift": dispatcher.is_on_shift,
    }