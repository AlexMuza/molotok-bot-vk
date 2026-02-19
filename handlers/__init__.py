"""
Регистрация всех обработчиков бота.
main.py вызывает register_all(bot), и каждый подмодуль вешает свои хендлеры.
"""
from . import callbacks, orders, start


def register_all(bot):
    """Подключает команду /start, кнопки (каталог, контакты, заказ) и приём заказов (текст)."""
    start.register(bot)
    callbacks.register(bot)
    orders.register(bot)
