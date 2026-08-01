import os
import logging
import json
import threading
from flask import Flask, request, jsonify, send_from_directory
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# ========== НАСТРОЙКИ ==========
TOKEN = "8702807148:AAEckteSCP32O7hx4Xv2MvrEjg4GI0DjbgY"
WEBAPP_URL = "https://shaurma-bot-4a6q.onrender.com/"
ADMIN_IDS = [963903929, 1253085905]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== FLASK ==========
app = Flask(__name__, static_folder='static', static_url_path='')

# ========== TELEGRAM BOT ==========
request_conn = HTTPXRequest(
    connect_timeout=60.0,
    read_timeout=60.0,
    write_timeout=60.0,
    pool_timeout=60.0
)
bot = Bot(token=TOKEN, request=request_conn)
application = Application.builder().token(TOKEN).request(request_conn).build()

# ========== ДАННЫЕ ==========
user_contacts = {}

# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard():
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [InlineKeyboardButton("📋 Меню и заказ", callback_data="menu")],
        [InlineKeyboardButton("📍 Контакты", callback_data="contacts")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ TELEGRAM ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🥙 Добро пожаловать, {user.first_name}!",
        reply_markup=get_main_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "menu":
        await query.edit_message_text(
            "🍔 Нажмите кнопку ниже, чтобы открыть меню:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🍔 Открыть меню", web_app={"url": WEBAPP_URL})]
            ])
        )
    elif query.data == "contacts":
        await query.edit_message_text("📍 ул. Большевистская, 151\n📞 +7 953 554 67 68")

async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Используйте кнопки.")

# ========== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ==========
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_handler))

# ========== ОБРАБОТЧИК WEBAPP_DATA ==========
@app.route('/webapp_data', methods=['POST'])
def handle_webapp_data():
    try:
        data = request.get_json()
        if not data or data.get('type') != 'order':
            return jsonify({'status': 'error'}), 400
        
        order_text = data.get('order', '')
        user_id = data.get('user_id')
        
        logger.info(f"🔥 ПОЛУЧЕН ЗАКАЗ: {order_text}")
        
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
            try:
                bot.send_message(
                    chat_id=user_id,
                    text=f"✅ Ваш заказ принят!\n\n{order_text}"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки пользователю: {e}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return jsonify({'status': 'error'}), 500

# ========== РАЗДАЧА СТАТИКИ ==========
@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ========== ЗАПУСК ПОЛЛИНГА В ОТДЕЛЬНОМ ПОТОКЕ ==========
def run_bot():
    logger.info("🤖 Бот запущен (polling)")
    application.run_polling()

# ========== ЗАПУСК FLASK ==========
if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Flask запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)