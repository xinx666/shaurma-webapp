import logging
import os
import threading
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# ========== НАСТРОЙКИ ==========
TOKEN = os.environ.get("TOKEN", "8702807148:AAEckteSCP32O7hx4Xv2MvrEjg4GI0DjbgY")
ADMIN_IDS = [963903929, 1253085905]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== ФАЛЬШИВЫЙ HTTP-СЕРВЕР ДЛЯ RENDER ==========
app = Flask(__name__)

@app.route('/')
def health_check():
    return "OK", 200

# ========== ОБРАБОТЧИК ЗАКАЗОВ ИЗ МИНИ-ПРИЛОЖЕНИЯ ==========
@app.route('/webapp_data', methods=['POST'])
def handle_webapp_data():
    try:
        data = request.get_json()
        if not data or data.get('type') != 'order':
            return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
        
        order_text = data.get('order', '')
        user_id = data.get('user_id')
        user_name = data.get('user_name', 'Клиент')
        user_phone = data.get('user_phone', 'не указан')
        
        logger.info(f"🔥 ПОЛУЧЕН ЗАКАЗ от {user_name} ({user_id}): {order_text}")
        
        bot = Bot(token=TOKEN)
        
        full_order_text = (
            f"🆕 **НОВЫЙ ЗАКАЗ!**\n\n"
            f"👤 Клиент: {user_name}\n"
            f"📱 Телефон: {user_phone}\n"
            f"🆔 ID: {user_id}\n"
            f"{'-' * 30}\n"
            f"{order_text}"
        )
        
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(
                    chat_id=admin_id,
                    text=full_order_text,
                    parse_mode="Markdown"
                )
                logger.info(f"✅ Заказ отправлен админу {admin_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки админу {admin_id}: {e}")
        
        if user_id:
            try:
                bot.send_message(
                    chat_id=user_id,
                    text=f"✅ **Ваш заказ принят!**\n\n{order_text}\n\n📍 **Самовывоз:** ул. Большевистская, 151",
                    parse_mode="Markdown"
                )
                logger.info(f"✅ Подтверждение отправлено пользователю {user_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки пользователю: {e}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def run_http_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# ========== ДАННЫЕ ==========
CONTACTS = {
    "address": "📍 ул. Большевистская, д. 151",
    "phone": "📞 +7 953 554 67 68",
    "hours": "🕐 11:00 - 22:00"
}

YANDEX_URL = "https://eda.yandex.ru/novosibirsk/r/saurma_-_i_tocka"
user_contacts = {}

# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 Меню и заказ", callback_data="menu")],
        [InlineKeyboardButton("📍 Контакты и адрес", callback_data="contacts")],
        [InlineKeyboardButton("📱 Заказать в Яндекс Еда", url=YANDEX_URL)],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_contact_keyboard():
    keyboard = [
        [KeyboardButton("📞 Отправить мой контакт", request_contact=True)],
        [KeyboardButton("✏️ Ввести номер вручную")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_back_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    logger.info(f"Пользователь {user_id} ({user.first_name}) запустил бота")
    
    # Сохраняем имя пользователя
    context.user_data['user_name'] = user.first_name
    context.user_data['user_id'] = user.id
    
    # Проверяем, есть ли уже контакт
    if user_id in user_contacts:
        # Если контакт уже есть — сразу показываем меню
        await update.message.reply_text(
            f"🥙 С возвращением, {user.first_name}!",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Если контакта нет — просим
    await update.message.reply_text(
        f"🥙 Здравствуйте, {user.first_name}!\n\n"
        "Добро пожаловать в 'Шаурма - и точка'! 🎉\n\n"
        "📱 **Для оформления заказа нам нужен ваш номер телефона.**\n\n"
        "Пожалуйста, поделитесь контактом, нажав кнопку ниже.\n"
        "Это займёт всего секунду, а мы сможем связаться с вами по заказу.\n\n"
        "Ваши данные в безопасности 🔒",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(
        "📞 **Нажмите кнопку, чтобы отправить контакт:**",
        reply_markup=get_contact_keyboard(),
        parse_mode="Markdown"
    )

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"Получен контакт от {user_id}: {contact.phone_number}")
    
    user_contacts[user_id] = {
        'phone': contact.phone_number,
        'first_name': contact.first_name,
        'last_name': contact.last_name or '',
    }
    
    await update.message.reply_text(
        f"✅ Спасибо, {contact.first_name}!\n"
        f"Ваш номер **{contact.phone_number}** сохранен.\n\n"
        "Теперь вы можете делать заказы! 🥙",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    
    # Отправляем уведомление админам
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📞 **Новый контакт!**\n👤 {contact.first_name}\n📱 {contact.phone_number}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу: {e}")
    
    await show_main_menu(update, context)

async def manual_contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    phone = update.message.text.strip()
    
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) < 10:
        await update.message.reply_text(
            "❌ Пожалуйста, введите корректный номер телефона.\nПример: +7 953 554 67 68",
            reply_markup=get_contact_keyboard()
        )
        return
    
    user_contacts[user_id] = {
        'phone': phone,
        'first_name': user.first_name or 'Клиент',
    }
    
    await update.message.reply_text(
        f"✅ Спасибо! Ваш номер **{phone}** сохранен.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📞 **Новый контакт (вручную)!**\n👤 {user.first_name}\n📱 {phone}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу: {e}")
    
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🥙 **Добро пожаловать в 'Шаурма - и точка'!**\n\n👇 Выберите действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == "menu":
        if user_id not in user_contacts:
            await query.edit_message_text(
                "⚠️ Для заказа нам нужен ваш контакт.\n"
                "Пожалуйста, нажмите /start и поделитесь контактом.",
                reply_markup=get_back_keyboard()
            )
            return
        
        await query.edit_message_text(
            "🥙 Нажмите кнопку ниже, чтобы открыть наше меню!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🍔 Открыть меню", web_app={"url": "https://shaurma-webapp.onrender.com/"})],
                [InlineKeyboardButton("🔙 Назад", callback_data="back")]
            ])
        )
    
    elif data == "contacts":
        contacts_text = f"{CONTACTS['address']}\n{CONTACTS['phone']}\n{CONTACTS['hours']}"
        await query.edit_message_text(
            f"📍 **Наш адрес**\n\n{contacts_text}",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "back":
        await query.edit_message_text(
            "🥙 Выберите действие:",
            reply_markup=get_main_keyboard()
        )

async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if text == "✏️ Ввести номер вручную":
        await update.message.reply_text(
            "📱 Введите ваш номер телефона:",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    if user_id in user_contacts:
        await update.message.reply_text(
            "😕 Я не понимаю это сообщение.\n\nПожалуйста, воспользуйтесь кнопками:",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "😕 Я не понимаю это сообщение.\n\nПожалуйста, отправьте контакт:",
            reply_markup=get_contact_keyboard()
        )

# ========== ЗАПУСК ==========
def main():
    # Запускаем фальшивый HTTP-сервер в отдельном потоке
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    logger.info("🌐 Фальшивый HTTP-сервер запущен для Render")

    # Запускаем бота
    request = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0
    )
    
    app_bot = Application.builder().token(TOKEN).request(request).build()
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app_bot.add_handler(MessageHandler(
        filters.Regex(r'^[\d\s\+\-\(\)]+$') & ~filters.COMMAND, 
        manual_contact_handler
    ))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_handler))
    
    print("=" * 50)
    print("🤖 Бот 'Шаурма - и точка' запущен!")
    print("📱 Откройте бота: https://t.me/ShawarmaTochkaBot")
    print("📋 Админы: " + ", ".join(str(a) for a in ADMIN_IDS))
    print("⏹️ Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    app_bot.run_polling()

if __name__ == "__main__":
    main()