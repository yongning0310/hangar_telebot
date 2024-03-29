#!/usr/bin/env python
import json
import logging
from company.command import check_quota, view_my_bookings, book_seats_handler, cancel_booking_handler
from telegram.ext import Application, CommandHandler
from data.data import load_data, save_data
from general_command import admin_conversation_handler, company_conversation_handler, start, logout
from general_command import start, admin_login, company_login
# from message_handler import handle_message
from admin.command import add_seat, add_company_handler, edit_company_handler, view_all_companies, view_all_seats, delete_company_handler, mark_seat_handler, view_avail_seats_handler, view_company_booking_handler, view_all_bookings
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import os
from config import TOKEN

# TOKEN = os.environ['TOKEN']

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

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

# havent tested this yet
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
    # Clean up last week's dates
    dates_to_delete = []
    for date in dates:
        if date < (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'):
            dates_to_delete.append(date)
    for date in dates_to_delete:
        del dates[date]


    # this should delete all bookings for the dates that are deleted 
    # this should also recover the quotas for the dates deleted 
    bookings_to_delete = []
    for company_id in data['bookings']:
        for booking in data['bookings'][company_id]:
            if booking['date'] in dates_to_delete:
                bookings_to_delete.append(booking)
    
    data['quotas'][booking['company_id']] += len(bookings_to_delete)

    # quota should be added all at once 
    for booking in bookings_to_delete:
        data['bookings'][booking['company_id']].remove(booking)


    save_data(data)


def add_login_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(admin_conversation_handler)
    application.add_handler(company_conversation_handler)

def add_admin_handlers(application):
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

def add_company_handlers(application):
    application.add_handler(CommandHandler("check_quota", check_quota)) 
    application.add_handler(book_seats_handler) 
    application.add_handler(CommandHandler("view_my_bookings", view_my_bookings))
    application.add_handler(cancel_booking_handler)


def main():
    application = Application.builder().token(TOKEN).build()

    add_login_handlers(application)
    add_admin_handlers(application)
    add_company_handlers(application)

    data = load_data()

    # Start the scheduler to add new dates every 14 days
    scheduler = BackgroundScheduler()
    scheduler.add_job(add_new_dates, 'interval', weeks=1, start_date=next_monday())
    scheduler.start()

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


