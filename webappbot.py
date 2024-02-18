#!/usr/bin/env python
import json
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext, ConversationHandler
from data.data import load_data
from general_command import ADMIN_PASSWORD, COMPANY_NAME, COMPANY_PASSWORD, admin_password_check, company_name_check, company_password_check, start, admin_login, company_login, cancel
from config import TOKEN


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Define conversation handler for admin login
admin_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('admin', admin_login)],
    states={
        ADMIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_password_check)],
    },
    fallbacks=[]
)

# Define conversation handler for company login
company_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('company', company_login)],
    states={
        COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_name_check)],
        COMPANY_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_password_check)],
    },
    fallbacks=[]
)

def main():
    application = Application.builder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(admin_conversation_handler)
    application.add_handler(company_conversation_handler)
    data = load_data()

    # # Placeholder handlers for admin and company commands
    # application.add_handler(CommandHandler("add_company", add_company))
    # application.add_handler(CommandHandler("edit_quota", edit_quota))
    # application.add_handler(CommandHandler("book_seat", book_seat))

    application.run_polling()

if __name__ == "__main__":
    main()



