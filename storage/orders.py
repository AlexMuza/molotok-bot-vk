"""
Логирование заказов: запись в текстовый файл (удобно смотреть) и в SQLite (удобно искать/анализировать).
"""
import sqlite3
from datetime import datetime
from pathlib import Path

# Импортируем пути из конфига после его инициализации
import config


def _ensure_data_dir():
    """Создаёт папку data, если её нет."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)


def _log_to_file(order_text: str, user_id: int, username: str | None, chat_id: int):
    """Добавляет одну строку в orders.log: дата, user_id, username, текст заказа."""
    _ensure_data_dir()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    username = username or ""
    # Одна строка на заказ, поля через табуляцию (удобно открыть в Excel)
    line = f"{ts}\t{user_id}\t{chat_id}\t{username}\t{order_text}\n"
    with open(config.ORDERS_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def _log_to_db(order_text: str, user_id: int, username: str | None, chat_id: int):
    """Сохраняет заказ в SQLite: таблица orders."""
    _ensure_data_dir()
    conn = sqlite3.connect(config.ORDERS_DB_FILE)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                username TEXT,
                order_text TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO orders (created_at, user_id, chat_id, username, order_text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                user_id,
                chat_id,
                username or "",
                order_text,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def save_order(order_text: str, user_id: int, username: str | None, chat_id: int) -> None:
    """
    Сохраняет заказ и в файл orders.log, и в БД orders.db.
    Вызывается из обработчика сообщений при каждом новом заказе.
    """
    _log_to_file(order_text, user_id, username, chat_id)
    _log_to_db(order_text, user_id, username, chat_id)
