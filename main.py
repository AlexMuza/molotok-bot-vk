"""
Точка входа: загрузка конфига, создание бота, регистрация обработчиков, запуск polling.
Запуск: из корня проекта выполнить  python main.py
"""
import config  # сразу загружает .env и проверяет TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID

from bot import bot
from handlers import register_all

if __name__ == "__main__":
    register_all(bot)
    print("Бот «Молоток» запущен.")
    print("Остановка: Ctrl+C")
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("Остановлено пользователем.")
    except Exception as e:
        print(f"Ошибка: {e}")
