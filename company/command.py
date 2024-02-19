from company.utils import is_valid_date_format, is_valid_date_range
from telegram.ext import Application, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, filters
from data.data import load_data, save_data
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from error_handler import handle_errors
from datetime import datetime

#view quota (total and used)
#view avail seats for all hours (by date) --> book by seat id, hour
#view all bookings (by date)
date_format_example = "YYYY-MM-DD"

# put this before every function call below, should raise error if not admin
def check_if_logged_on_as_company(update: Update, context: CallbackContext) -> bool:
    if context.user_data.get('role') == 'company':
        return True
    else:
        return False


# 1. Check quota
@handle_errors
async def check_quota(update: Update, context: CallbackContext) -> int:
    if not check_if_logged_on_as_company(update, context):
        await update.message.reply_text("You are not logged in as a company.")
        return ConversationHandler.END
    
    """Displays the quota and used seats for the company."""
    data = load_data()
    company_id = context.user_data["company"]["id"]
    print(company_id)
    company_quotas = data["quotas"][str(company_id)]
    total_quota = company_quotas["total_quota"]
    used_quota = company_quotas["quota_used"]
    await update.message.reply_text(f"Total quota: {total_quota}\nUsed quota: {used_quota}")
    return ConversationHandler.END

# 2. Book seats
DATE, BOOKING = range(2)
@handle_errors
async def book_seats(update: Update, context: CallbackContext) -> int:
    if not check_if_logged_on_as_company(update, context):
        await update.message.reply_text("You are not logged in as a company.")
        return ConversationHandler.END
    
    await update.message.reply_text("Please provide date in the format: " + date_format_example)
    return DATE


async def date(update: Update, context: CallbackContext) -> int:
    date_str = update.message.text
    """Books seats for the company."""
    data = load_data()
    if not is_valid_date_format(date_str):
        await update.message.reply_text("Please provide date in the format: " + date_format_example)
        return ConversationHandler.END

    if not is_valid_date_range(date_str, data):
        await update.message.reply_text(f"Date {date_str} is not within 7 days from today. Please enter a valid date.")
        return DATE

    await update.message.reply_text(f"Available seats for {date_str}. Every booking slot is 1 hour.")
    all_hours = data["dates"][date_str]
    seats_data = data["seats"]
    message = ""
    for hour, seats_dict in all_hours.items():
        available_seats = [
            seat_id for seat_id, seat_info in seats_dict.items()
            if seat_id in seats_data and not seat_info["is_booked"] and not seats_data[seat_id]["is_broken"]
        ]
        available_seats_str = ", ".join(available_seats)
        if available_seats:
            message += f"Hour: {hour}, Available seats: {available_seats_str}\n"
        else:
            message += f"Hour: {hour}, No available seats.\n"
    await update.message.reply_text(message)
    context.user_data["date"] = date_str
    await update.message.reply_text("Please enter the seat IDs and hours (in 24h format) to book the seats, separated by a semicolon. e.g. 1,2,3; 19:00, 20:00")
    return BOOKING

async def booking(update: Update, context: CallbackContext) -> int:
    data = load_data()
    date_str = context.user_data.get("date")
    company_id = str(context.user_data["company"]["id"])
    
    # Split the input into seats and times
    seats_times = update.message.text.split(";")
    if len(seats_times) != 2:
        await update.message.reply_text(f"Invalid input. Please enter the seat IDs and hours (in 24h format) to book the seats, separated by a semicolon. e.g. 1,2,3; 19:00, 20:00")
        return BOOKING
    
    seats = [str(seat.strip()) for seat in seats_times[0].split(",")]
    hours = [str(hour.strip()) for hour in seats_times[1].split(",")]
    
    # Check each seat for availability at each given time
    for seat_id in seats:
        for hour in hours:
            if seat_id not in data["seats"]:
                await update.message.reply_text(f"Invalid seat ID: {seat_id}.")
                return BOOKING
            if str(hour) not in list(data["dates"][date_str].keys()):
                await update.message.reply_text(f"Invalid hour: {hour}.")
                return BOOKING
            if not is_available_seat(seat_id, hour, date_str, data):
                await update.message.reply_text(f"Seat {seat_id} at {hour} on {date_str} is not available.")
                return BOOKING
    
    # Book all the available seats for all the available times
    for seat_id in seats:
        for hour in hours:
            data["dates"][date_str][hour][seat_id]["is_booked"] = True
            if company_id not in data["bookings"]:
                data["bookings"][company_id] = []
            data["bookings"][company_id].append({
                "date": date_str,
                "hour": hour,
                "seat_id": seat_id,
                "status": "confirmed"
            })
    
    # Book all the available seats for all the available times
    booked_seats_times = []
    for seat_id in seats:
        for hour in hours:
            data["dates"][date_str][hour][seat_id]["is_booked"] = True
            if company_id not in data["bookings"]:
                data["bookings"][company_id] = []
            data["bookings"][company_id].append({
                "date": date_str,
                "hour": hour,
                "seat_id": seat_id,
                "status": "confirmed"
            })
            booked_seats_times.append(f"Seat {seat_id} at {hour}")
    
    save_data(data)
    await update.message.reply_text(f"All seats have been booked for all the entered hours. Here are the details:\n" + "\n".join(booked_seats_times))
    return ConversationHandler.END

def is_available_seat(seat_id: str, hour: str, date: str, data) -> bool:
    return data["dates"][date][hour][seat_id]["is_booked"] == False and data["seats"][seat_id]["is_broken"] == False


async def cancel_book_seats(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Book Seats canceled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

book_seats_handler = ConversationHandler(
    entry_points=[CommandHandler('book_seats', book_seats)],
    states={DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, date)],
            BOOKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, booking)]},
    fallbacks=[CommandHandler('restart', cancel_book_seats)],
)

# 3. View existing bookings
@handle_errors
async def view_my_bookings(update: Update, context: CallbackContext) -> int:
    if not check_if_logged_on_as_company(update, context):
        await update.message.reply_text("You are not logged in as a company.")
        return ConversationHandler.END
    
    """Displays all existing bookings for the company."""
    data = load_data()
    company_id = str(context.user_data["company"]["id"])
    # {'company1': [{'date': '2024-02-20', 'hour': '09:00', 'seat_id': 'seat1'}, {'date': '2024-02-20', 'hour': '09:00', 'seat_id': 'seat2'}, 
    # {'date': '2024-02-20', 'hour': '09:00', 'seat_id': 'seat3'}], 'company2': [{'date': '2024-02-20', 'hour': '09:00', 'seat_id': 'seat2'}]}
    # the line below is wrong, what should it be 
    bookings = data["bookings"].get(company_id)
    if not bookings:
        await update.message.reply_text("No existing bookings.")
        return ConversationHandler.END
    bookings_str = "\n".join([f"Seat {booking['seat_id']} on {booking['date']} at {booking['hour']}" for booking in bookings])
    await update.message.reply_text(f"Existing bookings:\n{bookings_str}")
    return ConversationHandler.END