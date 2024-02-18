#!/usr/bin/env python
import json
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext, ConversationHandler
from data.data import load_data, save_data
from general_command import start, admin_login, company_login
from message_handler import handle_message
from config import TOKEN

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    application = Application.builder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_login))
    application.add_handler(CommandHandler("company", company_login))

    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # # Placeholder handlers for admin and company commands
    # application.add_handler(CommandHandler("add_company", add_company))
    # application.add_handler(CommandHandler("edit_quota", edit_quota))
    # application.add_handler(CommandHandler("book_seat", book_seat))

    application.run_polling()

if __name__ == "__main__":
    main()



