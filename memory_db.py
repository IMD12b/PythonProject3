# memory_db.py

ORDERS = []
COURIERS = [] # Теперь изначально пусто, курьеры будут добавляться сами

def add_order(order_data: dict):
    new_id = len(ORDERS) + 1
    order_data["id"] = new_id
    order_data["status"] = "🕒 Ожидает курьера"
    order_data["courier_name"] = None
    ORDERS.append(order_data)
    return new_id

def get_all_orders():
    return ORDERS

def get_order_by_id(order_id: int):
    for order in ORDERS:
        if order["id"] == order_id:
            return order
    return None

def get_all_couriers():
    return COURIERS

def get_courier_by_id(courier_id: int):
    for courier in COURIERS:
        if courier["id"] == courier_id:
            return courier
    return None

def get_courier_by_tg_id(tg_id: int):
    """Ищет курьера по его Telegram ID"""
    for courier in COURIERS:
        if courier["telegram_id"] == tg_id:
            return courier
    return None

def register_courier(tg_id: int, name: str, phone: str):
    """Добавляет нового курьера со статусом 'pending' (на модерации)"""
    new_id = len(COURIERS) + 1
    courier_data = {
        "id": new_id,
        "telegram_id": tg_id,
        "name": name,
        "phone": phone,
        "status": "pending",  # pending / approved / rejected
        "is_busy": False      # Занят ли он сейчас заказом
    }
    COURIERS.append(courier_data)
    return new_id

def update_courier_status(courier_id: int, new_status: str):
    """Меняет статус курьера (approved или rejected)"""
    courier = get_courier_by_id(courier_id)
    if courier:
        courier["status"] = new_status
        return True
    return False

def assign_courier(order_id: int, courier_id: int):
    order = get_order_by_id(order_id)
    courier = get_courier_by_id(courier_id)
    # Назначать можно только ПРИНЯТОГО курьера!
    if order and courier and courier["status"] == "approved":
        order["status"] = "🚚 В пути"
        order["courier_name"] = courier["name"]
        courier["is_busy"] = True
        return True
    return False