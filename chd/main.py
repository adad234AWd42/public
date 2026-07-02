from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from replit import db

TOKEN = "8997435200:AAE8Y8Txed21Z1CUHA6ZowglEKJCm26b1uI"
CHANNEL_ID = -1003871989923
SUPER_ADMIN_ID = 8441553990

WAITING_FOR_CONTENT, WAITING_FOR_USER_ID, WAITING_FOR_LIMIT = range(3)

def get_user_data(user_id):
    return db.get(str(user_id), {"limit": 1, "posts_today": 0})

def save_user_data(user_id, data):
    db[str(user_id)] = data

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != SUPER_ADMIN_ID and str(user_id) not in db:
        await update.message.reply_text("У вас нет доступа.")
        return

    buttons = [['Отправить пост']]
    if user_id == SUPER_ADMIN_ID:
        buttons.append(['Управление доступом'])
    
    await update.message.reply_text("Выберите действие:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

async def ask_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправьте фото, видео или текст. Для отмены напишите /cancel", reply_markup=ReplyKeyboardRemove())
    return WAITING_FOR_CONTENT

async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user_data(user_id)

    if user_id != SUPER_ADMIN_ID and data['posts_today'] >= data['limit']:
        await update.message.reply_text("Лимит постов исчерпан!")
        return ConversationHandler.END

    try:
        if update.message.photo:
            await context.bot.send_photo(CHANNEL_ID, update.message.photo[-1].file_id, caption=update.message.caption)
        elif update.message.video:
            await context.bot.send_video(CHANNEL_ID, update.message.video.file_id, caption=update.message.caption)
        else:
            await context.bot.send_message(CHANNEL_ID, update.message.text)
        
        data['posts_today'] += 1
        save_user_data(user_id, data)
        await update.message.reply_text("Опубликовано!")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")
    return ConversationHandler.END

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != SUPER_ADMIN_ID: return
    await update.message.reply_text("Введите ID пользователя:")
    return WAITING_FOR_USER_ID

async def set_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['target_id'] = update.message.text
    await update.message.reply_text("Введите лимит постов в день:")
    return WAITING_FOR_LIMIT

async def save_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_id = context.user_data['target_id']
    save_user_data(target_id, {"limit": int(update.message.text), "posts_today": 0})
    await update.message.reply_text(f"Пользователю {target_id} назначен лимит.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Text(["Отправить пост"]), ask_content),
            MessageHandler(filters.Text(["Управление доступом"]), admin_menu)
        ],
        states={
            WAITING_FOR_CONTENT: [MessageHandler(filters.COMMAND | filters.PHOTO | filters.VIDEO | filters.TEXT, publish)],
            WAITING_FOR_USER_ID: [MessageHandler(filters.TEXT, set_limit)],
            WAITING_FOR_LIMIT: [MessageHandler(filters.TEXT, save_admin)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
