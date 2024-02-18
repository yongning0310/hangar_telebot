#!/usr/bin/env python

import json
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext, ConversationHandler
from data.data import load_data, save_data
from general_command import start, admin_login, company_login
from message_handler import handle_message
from admin.command import add_seat, mark_seat_as_broken, view_avail_seats, edit_company_handler

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    application = Application.builder().token("6868552741:AAG-B_KtxRxYguBhHruZer0DP2PEfwkdnnQ").build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_login))
    application.add_handler(CommandHandler("company", company_login))

    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # # Placeholder handlers for admin and company commands
    application.add_handler(CommandHandler("add_seat", add_seat))
    application.add_handler(CommandHandler("mark_seat_as_broken", mark_seat_as_broken))
    application.add_handler(CommandHandler("view_avail_seats", view_avail_seats))
    application.add_handler(edit_company_handler)
    # application.add_handler(CommandHandler("book_seat", book_seat))

    application.run_polling()

if __name__ == "__main__":
    main()



