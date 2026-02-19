"""
Команда /start: приветствие и кнопки «Каталог», «Заказ», «Контакты».
"""
from telebot import types


def register(bot):
    @bot.message_handler(commands=["start"])
    def send_welcome(message):
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_catalog = types.InlineKeyboardButton("🛍️ Каталог", callback_data="catalog")
        btn_order = types.InlineKeyboardButton("📦 Заказ", callback_data="order")
        btn_contacts = types.InlineKeyboardButton("📞 Контакты", callback_data="contacts")
        markup.add(btn_catalog, btn_order, btn_contacts)

        welcome_text = """
<b>Добро пожаловать в магазин «Молоток»!</b>

Выберите нужный раздел:
        """
        bot.send_message(
            message.chat.id, welcome_text, parse_mode="html", reply_markup=markup
        )
