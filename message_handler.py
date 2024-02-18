from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext
from data.data import load_data, save_data


# Message Handlers
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    data = load_data()
    
    if text == data["admin_password"]:
        await update.message.reply_text("Admin authenticated. Available commands: /add_company, /edit_quota, /delete_company")
    elif text in data["companies"]:
        context.user_data["company_name"] = text
        await update.message.reply_text("Please enter your company password:")
    elif "company_name" in context.user_data and text == data["companies"][context.user_data["company_name"]]["password"]:
        await update.message.reply_text(f"Authenticated as {context.user_data['company_name']}. Use /book_seat to book a seat.")
    else:
        await update.message.reply_text("Invalid credentials or command.")