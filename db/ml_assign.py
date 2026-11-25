# db/ml_assign.py
import math


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def calculate_knn_distribution(new_orders, couriers, courier_loads):
    """
    new_orders: [{'id', 'ent_lat', 'ent_lon', 'cli_lat', 'cli_lon'}, ...]
    couriers:   [{'id', 'max_orders'}, ...]      # без lat/lon
    courier_loads: {courier_id: current_load}

    Возвращает: {order_id: courier_id}
    """
    if not new_orders or not couriers:
        return {}

    available = list(couriers)
    current_load = {c["id"]: courier_loads.get(c["id"], 0) for c in couriers}
    # «Стоимость» курьера — суммарная длина уже назначенных маршрутов
    current_cost = {c["id"]: 0.0 for c in couriers}
    assigned = {}

    # Длинные маршруты — первыми, чтобы не остались в конце
    orders_sorted = sorted(
        new_orders,
        key=lambda o: _haversine_km(o["ent_lat"], o["ent_lon"], o["cli_lat"], o["cli_lon"]),
        reverse=True,
    )

    for order in orders_sorted:
        route_len = _haversine_km(
            order["ent_lat"], order["ent_lon"], order["cli_lat"], order["cli_lon"]
        )
        best = None
        for c in available:
            limit = c.get("max_orders") or 5
            if current_load[c["id"]] >= limit:
                continue
            if best is None or current_cost[c["id"]] < current_cost[best["id"]]:
                best = c
        if best is None:
            break
        assigned[order["id"]] = best["id"]
        current_cost[best["id"]] += route_len
        current_load[best["id"]] += 1

    return assigned