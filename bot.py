import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# ========== НАСТРОЙКИ ==========
TOKEN = os.environ.get("TOKEN", "8702807148:AAEckteSCP32O7hx4Xv2MvrEjg4GI0DjbgY")
ADMIN_CHAT_ID = 963903929

# ========== СПИСОК АДМИНОВ (получают заказы) ==========
ADMIN_IDS = [
    963903929,  # ID первого админа
    1253085905, # ID второго админа
]

# ========== НАСТРОЙКИ МИНИ-ПРИЛОЖЕНИЯ ==========
WEBAPP_URL = "https://xinx666.github.io/shaurma-webapp/"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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
    
    logging.info(f"Пользователь {user_id} ({user.first_name}) запустил бота")
    
    if user_id in user_contacts:
        await update.message.reply_text(
            f"🥙 С возвращением, {user.first_name}!",
            reply_markup=get_main_keyboard()
        )
        return
    
    await update.message.reply_text(
        f"🥙 Здравствуйте, {user.first_name}!\n\n"
        "Добро пожаловать в 'Шаурма - и точка'! 🎉\n\n"
        "📱 **Для оформления заказа нам нужен ваш номер телефона.**\n\n"
        "Вы можете:\n"
        "• Нажать кнопку «Отправить мой контакт» — номер отправится автоматически\n"
        "• Или нажать «Ввести номер вручную» и написать его сами\n\n"
        "Ваши данные в безопасности 🔒",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(
        "📞 **Как хотите отправить контакт?**",
        reply_markup=get_contact_keyboard(),
        parse_mode="Markdown"
    )

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user
    user_id = user.id
    
    logging.info(f"Получен контакт от {user_id}: {contact.phone_number}")
    
    user_contacts[user_id] = {
        'phone': contact.phone_number,
        'first_name': contact.first_name,
        'last_name': contact.last_name or '',
        'user_id': user_id,
        'username': user.username or ''
    }
    
    await update.message.reply_text(
        f"✅ Спасибо, {contact.first_name}!\n"
        f"Ваш номер **{contact.phone_number}** сохранен.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"📞 **Новый контакт!**\n\n"
                f"👤 Имя: {contact.first_name} {contact.last_name or ''}\n"
                f"📱 Телефон: {contact.phone_number}\n"
                f"🆔 ID: {user_id}\n"
                f"👤 Username: @{user.username or 'не указан'}"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление админу: {e}")
    
    await show_main_menu(update, context)

async def manual_contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    phone = update.message.text.strip()
    
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) < 10:
        await update.message.reply_text(
            "❌ Пожалуйста, введите корректный номер телефона.\n"
            "Пример: +7 953 554 67 68 или 89535546768\n\n"
            "Попробуйте снова:",
            reply_markup=get_contact_keyboard()
        )
        return
    
    logging.info(f"Ручной ввод контакта от {user_id}: {phone}")
    
    user_contacts[user_id] = {
        'phone': phone,
        'first_name': user.first_name or 'Клиент',
        'last_name': user.last_name or '',
        'user_id': user_id,
        'username': user.username or ''
    }
    
    await update.message.reply_text(
        f"✅ Спасибо! Ваш номер **{phone}** сохранен.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"📞 **Новый контакт (вручную)!**\n\n"
                f"👤 Имя: {user.first_name} {user.last_name or ''}\n"
                f"📱 Телефон: {phone}\n"
                f"🆔 ID: {user_id}\n"
                f"👤 Username: @{user.username or 'не указан'}"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление админу: {e}")
    
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🥙 **Добро пожаловать в 'Шаурма - и точка'!**\n\n"
        "👇 Выберите действие:",
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
                "⚠️ Для заказа нам нужен ваш контакт.\n\n"
                "Пожалуйста, нажмите /start и поделитесь контактом.",
                reply_markup=get_back_keyboard()
            )
            return
        
        await query.edit_message_text(
            "🥙 Нажмите кнопку ниже, чтобы открыть наше меню!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="🍔 Открыть меню",
                    web_app={"url": WEBAPP_URL}
                )],
                [InlineKeyboardButton("🔙 Назад", callback_data="back")]
            ])
        )
    
    elif data == "contacts":
        contacts_text = (
            f"{CONTACTS['address']}\n"
            f"{CONTACTS['phone']}\n"
            f"{CONTACTS['hours']}\n\n"
            "🗺️ [Открыть карту](https://maps.google.com/maps?q=ул.+Большевистская,+151)"
        )
        
        try:
            with open("address.jpg", "rb") as photo_file:
                await query.message.reply_photo(
                    photo=photo_file,
                    caption=f"📍 **Наш адрес**\n\n{contacts_text}",
                    reply_markup=get_back_keyboard(),
                    parse_mode="Markdown"
                )
            await query.delete_message()
        except FileNotFoundError:
            await query.edit_message_text(
                f"📍 **Наш адрес**\n\n{contacts_text}",
                reply_markup=get_back_keyboard(),
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Ошибка при отправке фото: {e}")
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

async def webapp_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик данных из мини-приложения (заказы)"""
    logging.info("🔥🔥🔥 ПОЛУЧЕНЫ ДАННЫЕ ИЗ WEBAPP! 🔥🔥🔥")
    data = update.message.web_app_data
    if not data:
        logging.warning("⚠️ Данные пустые")
        return
    logging.info(f"📦 Данные: {data.data}")
    try:
        payload = json.loads(data.data)
        if payload.get('type') == 'order':
            order_text = payload.get('order', '')
            
            user = update.effective_user
            user_info = user_contacts.get(user.id, {})
            phone = user_info.get('phone', 'не указан')
            name = user_info.get('first_name', user.first_name or 'Клиент')
            
            full_order_text = (
                f"🆕 **НОВЫЙ ЗАКАЗ!**\n\n"
                f"👤 Клиент: {name}\n"
                f"📱 Телефон: {phone}\n"
                f"🆔 ID: {user.id}\n"
                f"👤 Username: @{user.username or 'не указан'}\n"
                f"{'-' * 30}\n"
                f"{order_text}"
            )
            
            await update.message.reply_text(
                f"✅ **Ваш заказ принят!**\n\n"
                f"{order_text}\n\n"
                f"📍 **Самовывоз:** ул. Большевистская, 151\n"
                f"🕐 Мы ждём вас к указанному времени!",
                parse_mode="Markdown"
            )
            
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=full_order_text,
                        parse_mode="Markdown"
                    )
                    logging.info(f"✅ Заказ отправлен админу {admin_id}")
                except Exception as e:
                    logging.error(f"❌ Не удалось отправить заказ админу {admin_id}: {e}")
            
            logging.info(f"🆕 Новый заказ от {user.id}")
        else:
            logging.warning("⚠️ Получены данные не типа 'order'")
    except json.JSONDecodeError:
        logging.error("❌ Не удалось распарсить данные из WebApp")

async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if text == "✏️ Ввести номер вручную":
        await update.message.reply_text(
            "📱 Введите ваш номер телефона:\nПример: +7 953 554 67 68 или 89535546768",
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
    request = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0
    )
    
    app = Application.builder().token(TOKEN).request(request).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(
        filters.Regex(r'^[\d\s\+\-\(\)]+$') & ~filters.COMMAND, 
        manual_contact_handler
    ))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_handler))
    
    print("=" * 50)
    print("🤖 Бот 'Шаурма - и точка' запущен!")
    print("📱 Откройте бота: https://t.me/ShawarmaTochkaBot")
    print("🍔 Мини-приложение: " + WEBAPP_URL)
    print("📋 Админы: " + ", ".join(str(a) for a in ADMIN_IDS))
    print("⏹️ Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    app.run_polling()

if __name__ == "__main__":
    main()