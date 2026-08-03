import os
import logging
import json
from flask import Flask, request, jsonify, send_from_directory
from telegram import Bot
from telegram.request import HTTPXRequest

# ========== НАСТРОЙКИ ==========
TOKEN = os.environ.get("TOKEN", "8702807148:AAEckteSCP32O7hx4Xv2MvrEjg4GI0DjbgY")
ADMIN_IDS = [963903929, 1253085905]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== FLASK ==========
app = Flask(__name__, static_folder='static', static_url_path='')

# ========== TELEGRAM BOT (только для отправки сообщений) ==========
request_conn = HTTPXRequest(
    connect_timeout=60.0,
    read_timeout=60.0,
    write_timeout=60.0,
    pool_timeout=60.0
)
bot = Bot(token=TOKEN, request=request_conn)

# ========== ОБРАБОТЧИК ЗАКАЗОВ ==========
@app.route('/webapp_data', methods=['POST'])
def handle_webapp_data():
    try:
        data = request.get_json()
        if not data or data.get('type') != 'order':
            return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
        
        order_text = data.get('order', '')
        user_id = data.get('user_id')
        
        logger.info(f"🔥 ПОЛУЧЕН ЗАКАЗ: {order_text}")
        
        # Отправляем заказ админам
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(
                    chat_id=admin_id,
                    text=f"🆕 НОВЫЙ ЗАКАЗ!\n\n{order_text}"
                )
                logger.info(f"✅ Заказ отправлен админу {admin_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки админу {admin_id}: {e}")
        
        # Отправляем подтверждение пользователю
        if user_id:
            try:
                bot.send_message(
                    chat_id=user_id,
                    text=f"✅ Ваш заказ принят!\n\n{order_text}"
                )
                logger.info(f"✅ Подтверждение отправлено пользователю {user_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки пользователю: {e}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ========== РАЗДАЧА СТАТИКИ ==========
@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Веб-приложение запущено на порту {port}")
    app.run(host='0.0.0.0', port=port)