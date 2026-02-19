"""
Обработка текстовых сообщений как заказов:
1) сохраняем заказ в файл и в БД,
2) отправляем подтверждение пользователю,
3) пересылаем заказ администратору в Telegram.
"""
import config
from storage.orders import save_order


def register(bot):
    @bot.message_handler(content_types=["text"])
    def handle_text(message):
        if message.text.startswith("/"):
            return  # команды не считаем заказом

        user_id = message.from_user.id if message.from_user else 0
        username = message.from_user.username if message.from_user else None
        chat_id = message.chat.id
        order_text = message.text

        # 1) Логирование: файл + SQLite
        save_order(order_text, user_id=user_id, username=username, chat_id=chat_id)

        # 2) Подтверждение клиенту
        order_response = f"""
✅ <b>Заказ принят!</b>

Мы получили ваш запрос:
"{order_text}"

Менеджер свяжется с вами в ближайшее время.

📞 Для срочных вопросов: +7 958 509-44-99
        """
        bot.send_message(message.chat.id, order_response, parse_mode="html")

        # 3) Пересылка администратору
        try:
            admin_text = (
                "📦 <b>Новый заказ</b>\n\n"
                f"👤 user_id: <code>{user_id}</code>\n"
                f"📛 username: @{username or '—'}\n"
                f"💬 Чат: <code>{chat_id}</code>\n\n"
                f"Текст заказа:\n{order_text}"
            )
            bot.send_message(
                config.ADMIN_CHAT_ID,
                admin_text,
                parse_mode="html",
            )
        except Exception as e:
            # Логируем ошибку, но пользователю уже отправили подтверждение
            print(f"Не удалось отправить заказ админу: {e}")
