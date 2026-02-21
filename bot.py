import csv
import os
import re
import sqlite3
import time
from datetime import datetime, timedelta

from dotenv import load_dotenv
from vkbottle import Keyboard, Text
from vkbottle.bot import Bot, Message

load_dotenv()

VK_BOT_TOKEN = os.getenv("VK_BOT_TOKEN", "")
MANAGER_ID = int(os.getenv("MANAGER_ID", "0"))

DUPLICATE_HOURS = 24
EXPORT_DIR = "exports"

if not VK_BOT_TOKEN or not MANAGER_ID:
    raise RuntimeError("Заполни VK_BOT_TOKEN и MANAGER_ID в .env")

bot = Bot(token=VK_BOT_TOKEN)
db = sqlite3.connect("shop.db")
db.row_factory = sqlite3.Row


def init_db() -> None:
    cur = db.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            price INTEGER NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            user_id INTEGER PRIMARY KEY,
            step TEXT NOT NULL DEFAULT 'idle',
            customer_name TEXT,
            phone TEXT,
            product_name TEXT,
            quantity INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            total_price INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'new'
        )
        """
    )
    db.commit()

    cur.execute("SELECT COUNT(*) AS cnt FROM products")
    if cur.fetchone()["cnt"] == 0:
        cur.executemany(
            "INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
            [
                ("молотки", "Прочный стальной молоток 500 г, прорезиненная ручка.", 890),
                ("гвозди", "Гвозди строительные 70 мм, упаковка 1 кг.", 320),
                ("перчатки", "Рабочие перчатки с усиленной ладонью.", 180),
            ],
        )
        db.commit()


def get_products():
    cur = db.cursor()
    cur.execute("SELECT name, description, price FROM products ORDER BY id")
    return cur.fetchall()


def get_product_by_name(name: str):
    cur = db.cursor()
    cur.execute("SELECT name, description, price FROM products WHERE name = ?", (name,))
    return cur.fetchone()


def get_or_create_session(user_id: int):
    cur = db.cursor()
    cur.execute("SELECT * FROM sessions WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if row:
        return row
    cur.execute("INSERT INTO sessions (user_id, step) VALUES (?, 'idle')", (user_id,))
    db.commit()
    cur.execute("SELECT * FROM sessions WHERE user_id = ?", (user_id,))
    return cur.fetchone()


def update_session(user_id: int, **fields):
    keys = ", ".join([f"{k} = ?" for k in fields.keys()])
    values = list(fields.values()) + [user_id]
    cur = db.cursor()
    cur.execute(f"UPDATE sessions SET {keys} WHERE user_id = ?", values)
    db.commit()


def reset_session(user_id: int):
    update_session(
        user_id,
        step="idle",
        customer_name=None,
        phone=None,
        product_name=None,
        quantity=None,
    )


def catalog_keyboard():
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("Каталог"))
    kb.add(Text("Заказать"))
    kb.row()
    kb.add(Text("Помощь"))
    return kb.get_json()


def products_keyboard():
    kb = Keyboard(one_time=False, inline=False)
    for p in get_products():
        kb.add(Text(p["name"]))
        kb.row()
    kb.add(Text("Назад"))
    return kb.get_json()


def quantity_keyboard():
    kb = Keyboard(one_time=True, inline=False)
    kb.add(Text("1"))
    kb.add(Text("2"))
    kb.add(Text("3"))
    kb.row()
    kb.add(Text("5"))
    kb.add(Text("10"))
    kb.row()
    kb.add(Text("Отмена"))
    return kb.get_json()


def normalize_phone(raw: str) -> str:
    cleaned = re.sub(r"[^\d+]", "", raw.strip())
    return cleaned


def is_valid_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone)
    return 10 <= len(digits) <= 15


def find_recent_duplicate(phone: str, product_name: str, hours: int = DUPLICATE_HOURS):
    since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    cur = db.cursor()
    cur.execute(
        """
        SELECT id, created_at, quantity, total_price
        FROM orders
        WHERE phone = ?
          AND product_name = ?
          AND created_at >= ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (phone, product_name, since),
    )
    return cur.fetchone()


def export_orders_to_csv() -> str:
    os.makedirs(EXPORT_DIR, exist_ok=True)
    filename = f"orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(EXPORT_DIR, filename)

    cur = db.cursor()
    cur.execute(
        """
        SELECT id, created_at, user_id, customer_name, phone, product_name, quantity, total_price, status
        FROM orders
        ORDER BY id DESC
        """
    )
    rows = cur.fetchall()

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(
            [
                "id",
                "created_at",
                "user_id",
                "customer_name",
                "phone",
                "product_name",
                "quantity",
                "total_price",
                "status",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r["id"],
                    r["created_at"],
                    r["user_id"],
                    r["customer_name"],
                    r["phone"],
                    r["product_name"],
                    r["quantity"],
                    r["total_price"],
                    r["status"],
                ]
            )

    return filepath


@bot.on.message()
async def handle_message(message: Message):
    if not message.text:
        return

    user_id = message.from_id
    text = message.text.strip()
    text_l = text.lower()

    session = get_or_create_session(user_id)
    step = session["step"]

    if text_l in {"отмена", "cancel"}:
        reset_session(user_id)
        await message.answer("Заявка отменена.", keyboard=catalog_keyboard())
        return

    if step == "await_name":
        update_session(user_id, customer_name=text, step="await_phone")
        await message.answer("Введи телефон (например, +79991234567):")
        return

    if step == "await_phone":
        phone = normalize_phone(text)
        if not is_valid_phone(phone):
            await message.answer("Телефон выглядит некорректно. Пример: +79991234567")
            return
        update_session(user_id, phone=phone, step="await_product")
        await message.answer("Выбери товар из каталога:", keyboard=products_keyboard())
        return

    if step == "await_product":
        product = get_product_by_name(text_l)
        if not product:
            await message.answer(
                "Такого товара нет. Выбери кнопкой:",
                keyboard=products_keyboard(),
            )
            return
        update_session(user_id, product_name=product["name"], step="await_quantity")
        await message.answer(
            f"Сколько штук товара '{product['name']}' нужно?",
            keyboard=quantity_keyboard(),
        )
        return

    if step == "await_quantity":
        if not text.isdigit() or int(text) <= 0:
            await message.answer("Количество должно быть положительным числом.")
            return

        qty = int(text)
        cur = db.cursor()
        cur.execute("SELECT * FROM sessions WHERE user_id = ?", (user_id,))
        s = cur.fetchone()
        product = get_product_by_name(s["product_name"])
        total = product["price"] * qty

        duplicate = find_recent_duplicate(s["phone"], s["product_name"])
        if duplicate:
            await message.answer(
                "Похоже, похожая заявка уже была недавно:\n"
                f"#{duplicate['id']} от {duplicate['created_at']}\n"
                f"Количество: {duplicate['quantity']}, сумма: {duplicate['total_price']} ₽\n\n"
                "Если нужен новый заказ — напиши 'Заказать' и измени количество/товар.",
                keyboard=catalog_keyboard(),
            )
            reset_session(user_id)
            return

        cur.execute(
            """
            INSERT INTO orders (created_at, user_id, customer_name, phone, product_name, quantity, total_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                user_id,
                s["customer_name"],
                s["phone"],
                s["product_name"],
                qty,
                total,
            ),
        )
        order_id = cur.lastrowid
        db.commit()

        manager_text = (
            f"Новая заявка #{order_id}\n"
            f"Имя: {s['customer_name']}\n"
            f"Телефон: {s['phone']}\n"
            f"Товар: {s['product_name']}\n"
            f"Количество: {qty}\n"
            f"Сумма: {total} ₽\n"
            f"VK user_id клиента: {user_id}"
        )

        await bot.api.messages.send(
            peer_id=MANAGER_ID,
            message=manager_text,
            random_id=int(time.time() * 1000) % 2_000_000_000,
        )

        reset_session(user_id)
        await message.answer(
            f"Готово! Заявка #{order_id} принята. Скоро с тобой свяжется менеджер.",
            keyboard=catalog_keyboard(),
        )
        return

    if text_l in {"начать", "start", "привет", "меню"}:
        await message.answer(
            "Привет! Я бот магазина.\n"
            "Команды: Каталог, Заказать, Помощь",
            keyboard=catalog_keyboard(),
        )
        return

    if text_l == "помощь":
        await message.answer(
            "Что я умею:\n"
            "1) Показать каталог\n"
            "2) Дать цену и описание\n"
            "3) Оформить заявку\n\n"
            "Напиши 'Каталог' или 'Заказать'.",
            keyboard=catalog_keyboard(),
        )
        return

    if text_l == "каталог":
        items = get_products()
        lines = ["Каталог:"]
        for p in items:
            lines.append(f"- {p['name']}: {p['price']} ₽")
        lines.append("\nНажми на товар, чтобы получить описание.")
        await message.answer("\n".join(lines), keyboard=products_keyboard())
        return

    if text_l == "заказать":
        update_session(user_id, step="await_name")
        await message.answer("Отлично, оформим заявку. Как тебя зовут?")
        return

    if text_l == "назад":
        await message.answer("Главное меню:", keyboard=catalog_keyboard())
        return

    if text_l == "экспорт":
        if user_id != MANAGER_ID:
            await message.answer("Команда доступна только менеджеру.")
            return
        path = export_orders_to_csv()
        await message.answer(f"Экспорт готов: {path}")
        return

    product = get_product_by_name(text_l)
    if product:
        await message.answer(
            f"{product['name'].capitalize()}\n"
            f"Цена: {product['price']} ₽\n"
            f"Описание: {product['description']}\n\n"
            "Чтобы купить, напиши: Заказать",
            keyboard=catalog_keyboard(),
        )
        return

    await message.answer(
        "Не понял команду. Напиши 'Каталог' или 'Заказать'.",
        keyboard=catalog_keyboard(),
    )


if __name__ == "__main__":
    init_db()
    bot.run_forever()
