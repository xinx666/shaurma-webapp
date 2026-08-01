import os
import logging
import json
from flask import Flask, request, jsonify, send_from_directory
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.request import HTTPXRequest

# ========== НАСТРОЙКИ ==========
TOKEN = os.environ.get("TOKEN", "8702807148:AAEckteSCP32O7hx4Xv2MvrEjg4GI0DjbgY")
WEBAPP_URL = "https://shaurma-bot-4a6q.onrender.com/"
ADMIN_IDS = [963903929, 1253085905]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== FLASK ==========
app = Flask(__name__, static_folder='static', static_url_path='')

# ========== СОЗДАЁМ СИНХРОННЫЙ BOT ==========
# Используем HTTPXRequest с таймаутами
request = HTTPXRequest(
    connect_timeout=30.0,
    read_timeout=30.0,
    write_timeout=30.0,
    pool_timeout=30.0
)
bot = Bot(token=TOKEN, request=request)

# ========== КЛАВИАТУРА ==========
def get_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 Меню и заказ", web_app={"url": WEBAPP_URL})],
        [InlineKeyboardButton("📍 Контакты", callback_data="contacts")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ ==========
def process_update(update_data):
    try:
        update = Update.de_json(update_data, bot)
        
        # Если это команда /start
        if update.message and update.message.text and update.message.text.startswith('/start'):
            user_id = update.effective_user.id
            logger.info(f"✅ Обрабатываю /start для {user_id}")
            
            # Синхронная отправка сообщения
            bot.send_message(
                chat_id=user_id,
                text="🥙 Добро пожаловать! Бот работает!",
                reply_markup=get_menu_keyboard()
            )
            return
        
        # Если это нажатие на кнопку
        if update.callback_query:
            query = update.callback_query
            user_id = query.from_user.id
            
            if query.data == "contacts":
                bot.send_message(
                    chat_id=user_id,
                    text="📍 ул. Большевистская, 151\n📞 +7 953 554 67 68"
                )
            return
        
        logger.info(f"⚠️ Неизвестное обновление: {update}")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")

# ========== МАРШРУТЫ ==========
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return "OK", 200
    
    try:
        data = request.get_json()
        if data:
            logger.info("📩 Получены данные")
            process_update(data)
        return "OK", 200
    except Exception as e:
        logger.error(f"❌ Ошибка в webhook: {e}")
        return "OK", 200

@app.route('/webapp_data', methods=['POST'])
def handle_webapp_data():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error'}), 400
        
        logger.info(f"🔥 ПОЛУЧЕН ЗАКАЗ: {data}")
        
        if data.get('type') == 'order':
            order_text = data.get('order', '')
            user_id = data.get('user_id')
            
            # Отправляем админам
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(
                        chat_id=admin_id,
                        text=f"🆕 НОВЫЙ ЗАКАЗ!\n\n{order_text}"
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки админу {admin_id}: {e}")
            
            # Подтверждение пользователю
            if user_id:
                bot.send_message(
                    chat_id=user_id,
                    text=f"✅ Заказ принят!\n\n{order_text}"
                )
            
            return jsonify({'status': 'success'}), 200
        
        return jsonify({'status': 'error'}), 400
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    # Устанавливаем webhook синхронно
    webhook_url = f"{WEBAPP_URL}webhook"
    try:
        bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)