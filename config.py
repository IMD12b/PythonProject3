# config.py
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")

# ← ДОБАВИТЬ
DATABASE_URL = os.getenv("DATABASE_URL")

_mod_ids_str = os.getenv("MODERATOR_IDS", "")
MODERATOR_IDS = [int(x.strip()) for x in _mod_ids_str.split(",") if x.strip()]

_admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in _admin_ids_str.split(",") if x.strip()]

# ← ДОБАВИТЬ проверку
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не задан в .env")

if __name__ == "__main__":
    print(f"Токен: {BOT_TOKEN[:5]}...")
    print(f"Админы: {ADMIN_IDS}")