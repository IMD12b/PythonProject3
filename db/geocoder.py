from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# 1. Создаем ОДИН раз на весь модуль (при запуске бота)
geolocator = Nominatim(user_agent="courier_delivery_bot_v1")

def get_coordinates(address: str) -> tuple[float, float] | None:
    """Превращает текстовый адрес в координаты"""
    try:
        # 2. Используем готовый объект внутри функции
        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
        return None
    except GeocoderTimedOut:
        return None
    except Exception as e:
        print(f"Ошибка геокодинга для адреса '{address}': {e}")
        return None