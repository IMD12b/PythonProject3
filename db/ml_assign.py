# db/ml_assign.py
import numpy as np
from sklearn.neighbors import KNeighborsClassifier


def calculate_knn_distribution(new_orders: list, couriers: list, courier_loads: dict) -> dict:
    """
    new_orders: список словарей [{'id': 1, 'lat': 55.75, 'lon': 37.61}, ...]
    couriers: список словарей [{'id': 10, 'max_orders': 5}, ...]
    courier_loads: словарь текущей загрузки {10: 2, 11: 0, ...}

    Возвращает: {order_id: courier_id} для тех заказов, которые нужно назначить.
    """
    # 1. Фильтруем курьеров, у которых есть место
    available_couriers = [c for c in couriers if courier_loads.get(c['id'], 0) < c['max_orders']]
    if not available_couriers or not new_orders:
        return {}

    # 2. Формируем "обучающую выборку" (центры)
    X_train = []
    y_train = []
    assigned_orders = {}  # {order_id: courier_id}

    # Копируем загрузку, чтобы не менять оригинал в процессе симуляции
    current_loads = courier_loads.copy()

    # Ищем по одному заказу для каждого доступного курьера
    for c in available_couriers:
        for order in new_orders:
            if order['id'] in assigned_orders:
                continue

            # Назначаем этот заказ как "якорь" для курьера
            X_train.append([order['lat'], order['lon']])
            y_train.append(c['id'])
            assigned_orders[order['id']] = c['id']
            current_loads[c['id']] = current_loads.get(c['id'], 0) + 1
            break  # Переходим к следующему курьеру

    if not X_train:
        return {}

    # 3. Обучаем KNN (k=1, ищем ближайшего соседа)
    # Для координат используем веса, чтобы ближайшие были важнее
    knn = KNeighborsClassifier(n_neighbors=1, weights='distance')
    knn.fit(X_train, y_train)

    # 4. Распределяем остальные заказы
    for order in new_orders:
        if order['id'] in assigned_orders:
            continue  # Этот заказ уже отдан как "якорь"

        # Предсказываем ближайшего курьера
        predicted_courier_id = int(knn.predict([[order['lat'], order['lon']]])[0])

        # Проверяем, есть ли у курьера место
        courier = next((c for c in available_couriers if c['id'] == predicted_courier_id), None)
        if courier and current_loads.get(courier['id'], 0) < courier['max_orders']:
            assigned_orders[order['id']] = courier['id']
            current_loads[courier['id']] += 1
        # Если места нет — заказ остается в пуле (мы его просто не добавляем в словарь)

    return assigned_orders