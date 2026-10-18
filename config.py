import os
from dotenv import load_dotenv

# Указываем абсолютный путь к .env (как мы делали в create)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Читаем токен
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Читаем прокси (если есть)
PROXY_URL = os.getenv("PROXY_URL")

_mod_ids_str = os.getenv("MODERATOR_IDS", "")
MODERATOR_IDS = [int(x.strip()) for x in _mod_ids_str.split(",") if x.strip()]
# Читаем админов и превращаем в список чисел
_admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in _admin_ids_str.split(",") if x.strip()]

# Проверка при запуске (выведет в консоль, чтобы ты видел, что всё ок)
if __name__ == "__main__":
    print(f"Токен: {BOT_TOKEN[:5]}...")
    print(f"Админы: {ADMIN_IDS}")