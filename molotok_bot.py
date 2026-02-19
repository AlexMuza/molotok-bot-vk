




import telebot
from telebot import types

# Ваш токен от BotFather
API_TOKEN = '7963014305:AAGTKTxiolkgrkIUhywGeFVzS1GI_9IU0T'
bot = telebot.TeleBot(API_TOKEN)

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_catalog = types.InlineKeyboardButton("🛍️ Каталог", callback_data='catalog')
    btn_order = types.InlineKeyboardButton("📦 Заказ", callback_data='order') 
    btn_contacts = types.InlineKeyboardButton("📞 Контакты", callback_data='contacts')
    
    markup.add(btn_catalog, btn_order, btn_contacts)
    
    welcome_text = """
<b>Добро пожаловать в магазин «Молоток»!</b>

Выберите нужный раздел:
    """
    bot.send_message(message.chat.id, welcome_text, parse_mode='html', reply_markup=markup)

# Обработка нажатий кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    if call.data == 'contacts':
        contacts_text = """
🏪 <b>МАГАЗИН «МОЛОТОК»</b>

📍 <b>АДРЕС:</b> г. Воронеж, ул. Электровозная, дом 25Д
📞 <b>ТЕЛЕФОН:</b> +7 958 509-44-99
🕒 <b>ВРЕМЯ РАБОТЫ:</b> Пн-Вс 8:00-19:00

🚚 <b>ДОСТАВКА:</b> По Воронежу 300 руб.
        """
        bot.send_message(call.message.chat.id, contacts_text, parse_mode='html')
    
    elif call.data == 'catalog':
        catalog_text = """
🛍️ <b>КАТАЛОГ ТОВАРОВ</b>

🎨 <b>Краски и лаки:</b>
• Водоэмульсионные
• Алкидные эмали
• Грунтовки

🛠️ <b>Инструменты:</b>
• Шуруповерты
• Молотки, отвертки
• Измерительные

🔩 <b>Крепеж:</b>
• Саморезы, дюбели
• Гвозди, болты
• Замки, ручки

🏡 <b>Для сада и огорода:</b>
• Утеплители
• Садовый инструмент
        """
        bot.send_message(call.message.chat.id, catalog_text, parse_mode='html')
    
    elif call.data == 'order':
        order_text = """
📦 <b>ПРЕДВАРИТЕЛЬНЫЙ ЗАКАЗ</b>

Напишите что хотите заказать и ваш номер телефона.

<b>Пример:</b> 
"Краска белая 10л - 2 банки, +79101234567"

✅ Менеджер свяжется в течение 15 минут!
        """
        bot.send_message(call.message.chat.id, order_text, parse_mode='html')

# Обработка текстовых сообщений (для заказов)
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if not message.text.startswith('/'):
        # Если сообщение не команда, считаем что это заказ
        order_response = f"""
✅ <b>Заказ принят!</b>

Мы получили ваш запрос:
"{message.text}"

Менеджер свяжется с вами в ближайшее время.

📞 Для срочных вопросов: +7 958 509-44-99
        """
        bot.send_message(message.chat.id, order_response, parse_mode='html')

# Запуск бота
if __name__ == '__main__':
    print("Бот 'Молоток' запущен...")
    print("Для остановки нажмите Ctrl+C")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Ошибка: {e}")