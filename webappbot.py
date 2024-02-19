#!/usr/bin/env python
import json
import logging
from company.command import check_quota, view_my_bookings, book_seats_handler
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext, ConversationHandler
from data.data import load_data, save_data
from general_command import ADMIN_PASSWORD, COMPANY_NAME, COMPANY_PASSWORD, admin_password_check, company_name_check, company_password_check, start, admin_login, company_login, logout
from general_command import start, admin_login, company_login
# from message_handler import handle_message
from admin.command import add_seat, add_company_handler, edit_company_handler, view_all_companies, view_all_seats, delete_company_handler, mark_seat_handler, view_avail_seats_handler, view_company_booking_handler, view_all_bookings
from config import TOKEN
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Define conversation handler for admin login
admin_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('admin', admin_login)],
    states={
        ADMIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_password_check)],
    },
    fallbacks=[CommandHandler('restart', logout)]
)

# Define conversation handler for company login
company_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('company', company_login)],
    states={
        COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_name_check)],
        COMPANY_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_password_check)],
    },
    fallbacks=[CommandHandler('restart', logout)]
)

def reset_data():
    '''reset the data to the initial state'''
    logger.info("Resetting data")
    data = load_data()
    #next-id
    data["next_company_id"] = "1"
    #discarded_id
    data["discarded_company_id_nums"] = []
    #admin
    data["admin"] = { "id": "admin1", "password": "hangar_admin" }
    #companies
    data["companies"] = {} #company id to its info
    #dates
    data["dates"] = {} #date to its hours
    #seats
    data["seats"] = {} #seat id to its info
    #bookings
    data["bookings"] = {} #company id to its bookings
    #quotas
    data["quotas"] = {} #company id to its quotas
    save_data(data)
    add_new_dates(14)

def add_new_dates(num_days=7):
    # Adds new dates for the next 14 days to the database, initializing the seats for each date and hour
    data = load_data()
    dates = data['dates']
    for i in range(num_days):
        date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
        if date not in dates:
            dates[date] = {}
            for hour in range(0, 24):
                # Format the hour as a datetime string
                hour_str = datetime.strptime(str(hour), "%H").strftime("%H:%M")
                dates[date][hour_str] = {}
                for seat_id in data['seats']:
                    if data['seats'][seat_id]['is_broken'] == True:
                        continue
                    dates[date][hour_str][seat_id] = {"is_booked": False}
    save_data(data)
    # Clean up last week's dates
    dates_to_delete = []
    for date in dates:
        if date < (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'):
            dates_to_delete.append(date)
    for date in dates_to_delete:
        del dates[date]
    
def main():
    reset_data()
    application = Application.builder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(admin_conversation_handler)
    application.add_handler(company_conversation_handler)
    
    data = load_data()

    # # Placeholder handlers for admin and company commands
    application.add_handler(CommandHandler('add_seat', add_seat))
    application.add_handler(mark_seat_handler)
    application.add_handler(view_avail_seats_handler)
    application.add_handler(add_company_handler)
    application.add_handler(delete_company_handler)
    application.add_handler(edit_company_handler)
    application.add_handler(CommandHandler('view_all_companies', view_all_companies)) 
    application.add_handler(CommandHandler('view_all_seats', view_all_seats))
    application.add_handler(CommandHandler('view_all_bookings', view_all_bookings))
    
    application.add_handler(view_company_booking_handler)
    # application.add_handler(CommandHandler("book_seat", book_seat))
        # # Placeholder handlers for admin and company commands
    application.add_handler(CommandHandler("check_quota", check_quota)) 
    application.add_handler(book_seats_handler) 
    application.add_handler(CommandHandler("view_my_bookings", view_my_bookings))

    # Start the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(add_new_dates, 'interval', weeks=1, start_date=next_monday())
    scheduler.start()

    # add_new_dates()
    application.run_polling()

def next_monday():
    # Get the current date
    now = datetime.now()

    # Get the number of days until next Monday
    days_until_monday = (7 - now.weekday() or 7)

    # Get the date of next Monday
    next_monday = now + timedelta(days=days_until_monday)

    return next_monday

if __name__ == "__main__":
    main()


