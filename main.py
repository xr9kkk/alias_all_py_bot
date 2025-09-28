from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
import os
import html
from dotenv import load_dotenv

load_dotenv()

MEMBERS_FILE = 'members.json'

def load_members():
    if os.path.exists(MEMBERS_FILE):
        with open(MEMBERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_member(chat_id, user_id, username, first_name, is_bot=False):
    
    if is_bot:
        return
    
    members = load_members()
    
    chat_key = str(chat_id)
    user_key = str(user_id)
    
    if chat_key not in members:
        members[chat_key] = {}
    
    members[chat_key][user_key] = {
        'username': username,
        'first_name': first_name or 'Участник'
    }
    
    with open(MEMBERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(members, f, ensure_ascii=False, indent=2)

def get_all_members(chat_id):
    members = load_members()
    chat_key = str(chat_id)
    return members.get(chat_key, {})

def create_safe_mention_text(members):
    if not members:
        return "❌ Нет участников для упоминания"
    
    mentions = []
    for user_id, user_data in members.items():
        username = user_data.get('username')
        first_name = user_data.get('first_name', 'Участник')
        
        safe_first_name = html.escape(first_name)
        
        if username:
            mentions.append(f"@{username}")
        else:
            mentions.append(f"👤 {safe_first_name} (ID: {user_id})")
    
    return " ".join(mentions)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Бот для упоминания всех участников!\n\n"
        "Просто напишите @all в любом сообщении, и бот упомянет всех участников чата.\n\n"
        "Бот запоминает участников, когда они пишут сообщения."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Помощь по боту:\n\n"
        "• Напишите @all в любом сообщении - упомянутся все участники\n"
        "• Бот автоматически запоминает новых участников\n"
        "• Участники без username будут упомянуты по имени\n"
        "• Боты исключаются из упоминаний\n\n"
        "Команды:\n"
        "/start - начать работу\n"
        "/help - эта справка\n"
        "/members - показать список участников"
    )

async def members_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                member_list += f"• {first_name} (ID: {user_id})\n"
        
        await update.message.reply_text(member_list)
    else:
        await update.message.reply_text("❌ Нет сохраненных участников. Начните общение в чате!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    chat_id = update.message.chat_id
    user = update.message.from_user
    
    save_member(chat_id, user.id, user.username, user.first_name, user.is_bot)
    
    if '@all' in update.message.text.lower():
        members = get_all_members(chat_id)
        
        if members:
            mention_text = create_safe_mention_text(members)
            
            await update.message.reply_text(
                f"📢 Упоминание всех участников!\n\n{mention_text}"
            )
        else:
            await update.message.reply_text(
                "❌ Нет сохраненных участников. Подождите, пока участники напишут сообщения."
            )

async def track_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.new_chat_members:
        chat_id = update.message.chat_id
        
        human_users = [user for user in update.message.new_chat_members if not user.is_bot]
        bot_users = [user for user in update.message.new_chat_members if user.is_bot]
        
        for user in human_users:
            save_member(chat_id, user.id, user.username, user.first_name, user.is_bot)
        
        if human_users:
            new_members = ", ".join([f"@{user.username}" if user.username else user.first_name 
                                   for user in human_users])
            
            welcome_text = f"👋 Добро пожаловать, {new_members}!\n\nБот запомнил вас для упоминаний @all"
            
            if bot_users:
                bot_names = ", ".join([f"@{user.username}" if user.username else user.first_name 
                                     for user in bot_users])
                welcome_text += f"\n\n🤖 Также добавлены боты: {bot_names} (не участвуют в упоминаниях)"
            
            await update.message.reply_text(welcome_text)

async def cleanup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    try:
        chat_member = await context.bot.get_chat_member(chat_id, update.message.from_user.id)
        
        if chat_member.status in ['administrator', 'creator']:
            members = load_members()
            chat_key = str(chat_id)
            
            if chat_key in members:
                count_before = len(members[chat_key])
                
                members[chat_key] = {}
                
                with open(MEMBERS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(members, f, ensure_ascii=False, indent=2)
                
                await update.message.reply_text(
                    f"✅ Список участников очищен! Удалено {count_before} участников.\n"
                    f"Участники будут добавляться заново при написании сообщений."
                )
            else:
                await update.message.reply_text("❌ Нет сохраненных участников для этого чата.")
        else:
            await update.message.reply_text("❌ Эта команда только для администраторов.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при выполнении команды: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Произошла ошибка: {context.error}")
    
    if update and update.message:
        try:
            await update.message.reply_text("❌ Произошла ошибка при обработке запроса")
        except:
            pass

def main():
    TOKEN = os.getenv('BOT_TOKEN')
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("members", members_command))
    application.add_handler(CommandHandler("cleanup", cleanup_command))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_new_members))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.add_error_handler(error_handler)
    
    print("🟢 Бот запущен и готов к работе!")
    print("🤖 Бот исключает себя и других ботов из упоминаний")
    print("🛡️  Используется безопасный режим отправки сообщений")
    print("⏹️  Для остановки нажмите Ctrl+C")
    
    application.run_polling()

if __name__ == '__main__':
    main()