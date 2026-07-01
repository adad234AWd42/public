cat << 'EOF' > main.py
import json
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.request import HTTPXRequest
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = "8997435200:AAE8Y8Txed21Z1CUHA6ZowglEKJCm26b1uI"
CHANNEL_ID = -1003871989923
SUPER_ADMIN_ID = 8441553990
DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

def get_user_data(user_id):
    db = load_db()
    return db.get(str(user_id), {"limit": 1, "posts_today": 0})

def save_user_data(user_id, data):
    db = load_db()
    db[str(user_id)] = data
    save_db(db)

WAITING_FOR_CONTENT, WAITING_FOR_USER_ID, WAITING_FOR_LIMIT = range(3)

async def start(update, context):
    user_id = update.effective_user.id
    db = load_db()
    if user_id != SUPER_ADMIN_ID and str(user_id) not in db:
        await update.message.reply_text("У вас нет доступа.")
        return
    buttons = [['Отправить пост']]
    if user_id == SUPER_ADMIN_ID:
        buttons.append(['Управление доступом'])
    await update.message.reply_text("Выберите действие:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

async def ask_content(update, context):
    await update.message.reply_text("Отправьте фото, видео или текст.", reply_markup=ReplyKeyboardRemove())
    return WAITING_FOR_CONTENT

async def publish(update, context):
    user_id = update.effective_user.id
    data = get_user_data(user_id)
    if user_id != SUPER_ADMIN_ID and data['posts_today'] >= data['limit']:
        await update.message.reply_text("Лимит исчерпан!")
        return ConversationHandler.END
    if update.message.photo:
        await context.bot.send_photo(CHANNEL_ID, update.message.photo[-1].file_id, caption=update.message.caption)
    elif update.message.video:
        await context.bot.send_video(CHANNEL_ID, update.message.video.file_id, caption=update.message.caption)
    else:
        await context.bot.send_message(CHANNEL_ID, update.message.text)
    data['posts_today'] += 1
    save_user_data(user_id, data)
    await update.message.reply_text("Опубликовано!")
    return ConversationHandler.END

async def admin_menu(update, context):
    if update.effective_user.id != SUPER_ADMIN_ID: return
    await update.message.reply_text("Введите ID пользователя:")
    return WAITING_FOR_USER_ID

async def set_limit(update, context):
    context.user_data['target_id'] = update.message.text
    await update.message.reply_text("Введите лимит:")
    return WAITING_FOR_LIMIT

async def save_admin(update, context):
    target_id = context.user_data['target_id']
    save_user_data(target_id, {"limit": int(update.message.text), "posts_today": 0})
    await update.message.reply_text("Лимит назначен.")
    return ConversationHandler.END

async def cancel(update, context):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

def main():
    proxy = "socks5://user335792:9etya2@194.59.8.25:19208"
    req = HTTPXRequest(proxy_url=proxy)
    app = Application.builder().token(TOKEN).request(req).build()
    
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Text(["Отправить пост"]), ask_content),
            MessageHandler(filters.Text(["Управление доступом"]), admin_menu)
        ],
    states={
            WAITING_FOR_CONTENT: [MessageHandler(filters.PHOTO | filters.VIDEO | filters.TEXT, publish)],
            WAITING_FOR_USER_ID: [MessageHandler(filters.TEXT, set_limit)],
            WAITING_FOR_LIMIT: [MessageHandler(filters.TEXT, save_admin)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
EOF
