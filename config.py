"""
Конфигурация бота из переменных окружения.
Токен и ID админа не хранятся в коде — только в .env (или в системе).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env из папки проекта (рядом с config.py)
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)


def _get_required(key: str, description: str) -> str:
    """Читает обязательную переменную окружения. Выходит с понятной ошибкой, если нет."""
    value = os.environ.get(key, "").strip()
    if not value:
        print(
            f"Ошибка: не задана переменная окружения {key}.\n"
            f"  {description}\n"
            f"  Создайте файл .env (скопируйте из .env.example) и заполните значения."
        )
        raise SystemExit(1)
    return value


# Токен бота (обязательно)
TELEGRAM_BOT_TOKEN = _get_required(
    "TELEGRAM_BOT_TOKEN",
    "Токен выдаёт @BotFather в Telegram.",
)

# ID чата администратора — сюда пересылаются заказы (обязательно для пересылки)
ADMIN_CHAT_ID = _get_required(
    "ADMIN_CHAT_ID",
    "Узнать ID: напишите боту @userinfobot в Telegram, скопируйте 'Id'.",
)

# Папка для логов и БД (можно задать через env, по умолчанию — data в корне проекта)
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", str(BASE_DIR / "data")))
ORDERS_LOG_FILE = DATA_DIR / "orders.log"
ORDERS_DB_FILE = DATA_DIR / "orders.db"
