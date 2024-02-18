#!/usr/bin/env python
import json
import logging
from company.command import book_seats, check_quota, view_existing_bookings
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext, ConversationHandler
from data.data import load_data, save_data
from general_command import ADMIN_PASSWORD, COMPANY_NAME, COMPANY_PASSWORD, admin_password_check, company_name_check, company_password_check, start, admin_login, company_login, logout
from admin.command import add_seat, mark_seat_as_broken, view_avail_seats, edit_company_handler
from general_command import start, admin_login, company_login
# from message_handler import handle_message
from admin.command import add_seat, mark_seat_as_broken, view_avail_seats, add_company_handler, delete_company, edit_company_handler, view_all_companies, view_company, view_all_seats
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
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(admin_conversation_handler)
    application.add_handler(company_conversation_handler)
    data = load_data()

    # # Placeholder handlers for admin and company commands
    application.add_handler(CommandHandler('add_seat', add_seat))
    application.add_handler(CommandHandler('mark_seat_as_broken', mark_seat_as_broken))
    application.add_handler(CommandHandler('view_avail_seats', view_avail_seats))
    application.add_handler(add_company_handler)
    application.add_handler(CommandHandler('delete_company', delete_company))
    application.add_handler(edit_company_handler)
    application.add_handler(CommandHandler('view_all_companies', view_all_companies))
    application.add_handler(CommandHandler('view_company', view_company))
    application.add_handler(CommandHandler('view_all_seats', view_all_seats))
    # application.add_handler(CommandHandler("book_seat", book_seat))
        # # Placeholder handlers for admin and company commands
    application.add_handler(CommandHandler("check_quota", check_quota))
    application.add_handler(CommandHandler("book_seats", book_seats))
    application.add_handler(CommandHandler("view_existing_bookings", view_existing_bookings))

    application.run_polling()

if __name__ == "__main__":
    main()


