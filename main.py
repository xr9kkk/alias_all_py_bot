from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
import os

# Файл для хранения данных
MEMBERS_FILE = 'members.json'

def load_members():
    """Загружаем данные из файла"""
    if os.path.exists(MEMBERS_FILE):
        with open(MEMBERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_member(chat_id, user_id, username, first_name):
    """Сохраняем информацию о пользователе"""
    members = load_members()
    
    # Преобразуем ID в строки для JSON
    chat_key = str(chat_id)
    user_key = str(user_id)
    
    if chat_key not in members:
        members[chat_key] = {}
    
    # Сохраняем данные пользователя
    members[chat_key][user_key] = {
        'username': username,
        'first_name': first_name or 'Участник'
    }
    
    # Записываем в файл
    with open(MEMBERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(members, f, ensure_ascii=False, indent=2)

def get_all_members(chat_id):
    """Получаем всех участников чата"""
    members = load_members()
    chat_key = str(chat_id)
    return members.get(chat_key, {})

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "🤖 Бот для упоминания всех участников!\n\n"
        "Просто напишите @all в любом сообщении, и бот упомянет всех участников чата.\n\n"
        "Бот запоминает участников, когда они пишут сообщения."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "📖 Помощь по боту:\n\n"
        "• Напишите @all в любом сообщении - упомянутся все участники\n"
        "• Бот автоматически запоминает новых участников\n"
        "• Участники без username будут упомянуты по имени\n\n"
        "Команды:\n"
        "/start - начать работу\n"
        "/help - эта справка\n"
        "/members - показать список участников"
    )

async def members_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /members - показать список участников"""
    chat_id = update.message.chat_id
    members = get_all_members(chat_id)
    
    if members:
        member_list = "📋 Список участников:\n\n"
        for user_id, user_data in members.items():
            username = user_data.get('username')
            first_name = user_data.get('first_name', 'Участник')
            
            if username:
                member_list += f"• @{username} ({first_name})\n"
            else:
                member_list += f"• {first_name} (без username)\n"
        
        await update.message.reply_text(member_list)
    else:
        await update.message.reply_text("❌ Нет сохраненных участников. Начните общение в чате!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех сообщений"""
    if not update.message or not update.message.text:
        return
    
    chat_id = update.message.chat_id
    user = update.message.from_user
    
    # Сохраняем информацию об отправителе
    save_member(chat_id, user.id, user.username, user.first_name)
    
    # Проверяем наличие @all в сообщении
    if '@all' in update.message.text.lower():
        # Получаем всех участников чата
        members = get_all_members(chat_id)
        
        if members:
            mentions = []
            for user_id, user_data in members.items():
                username = user_data.get('username')
                first_name = user_data.get('first_name', 'Участник')
                
                if username:
                    mentions.append(f"@{username}")
                else:
                    mentions.append(f"[{first_name}](tg://user?id={user_id})")
            
            # Собираем текст упоминания
            mention_text = " ".join(mentions)
            
            # Отправляем упоминание (реплаем на оригинальное сообщение)
            await update.message.reply_text(
                f"📢 **Упоминание всех участников!**\n\n{mention_text}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ Нет сохраненных участников. Подождите, пока участники напишут сообщения."
            )

async def track_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отслеживаем новых участников"""
    if update.message.new_chat_members:
        chat_id = update.message.chat_id
        
        for user in update.message.new_chat_members:
            # Сохраняем информацию о новых участниках
            save_member(chat_id, user.id, user.username, user.first_name)
        
        # Приветствуем новых участников
        new_members = ", ".join([f"@{user.username}" if user.username else user.first_name 
                               for user in update.message.new_chat_members])
        
        await update.message.reply_text(
            f"👋 Добро пожаловать, {new_members}!\n\n"
            f"Бот запомнил вас для упоминаний @all"
        )

def main():
    """Основная функция"""
    # ЗАМЕНИТЕ 'YOUR_BOT_TOKEN' на реальный токен!
    TOKEN = "7824236122:AAHpTPxaFfJZudfRS9i1tD5EjJtg04uN2zo"
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("members", members_command))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_new_members))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    print("🟢 Бот запущен и готов к работе!")
    print("⏹️  Для остановки нажмите Ctrl+C")
    
    application.run_polling()

if __name__ == '__main__':
    main()