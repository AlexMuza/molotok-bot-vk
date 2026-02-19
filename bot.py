"""
Создание экземпляра бота. Токен берётся из config (переменные окружения).
Регистрация хендлеров выполняется в main.py через handlers.register_all(bot).
"""
import telebot

import config

# Безопасный запуск: токен только из .env, не из кода
bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN)
