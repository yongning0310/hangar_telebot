from telegram.ext import Application, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, filters
from data.data import load_data, save_data
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

#view quota (total and used)
#view avail seats for all hours (by date) --> book by seat id, hour
#view all bookings (by date)

# put this before every function call below, should raise error if not admin
def check_if_logged_on_as_company(update: Update, context: CallbackContext) -> bool:
    if context.user_data.get('role') == 'company':
        return True
    else:
        return False
    
# 1. Check quota
async def check_quota(update: Update, context: CallbackContext) -> int:
    if not check_if_logged_on_as_company(update, context):
        await update.message.reply_text("You are not logged in as a company.")
        return ConversationHandler.END
    
    """Displays the quota and used seats for the company."""
    data = load_data()
    company_id = context.user_data["company"]["id"]
    company_quotas = data["quotas"][company_id]
    total_quota = company_quotas["total_quota"]
    used_quota = company_quotas["quota_used"]
    await update.message.reply_text(f"Total quota: {total_quota}\nUsed quota: {used_quota}")
    return ConversationHandler.END

# 2. Book seats
async def book_seats(update: Update, context: CallbackContext) -> int:
    if not check_if_logged_on_as_company(update, context):
        await update.message.reply_text("You are not logged in as a company.")
        return ConversationHandler.END
    
    
    """Books seats for the company."""
    data = load_data()
    if not context.args:
        await update.message.reply_text("Please provide date in the format: " + date_format_example)
        return ConversationHandler.END
    date = context.args[0]
    avail_seats = [seat for seat in data["seats"] if seat["is_broken"] == False]
    if not avail_seats:
        await update.message.reply_text("No available seats.")
        return ConversationHandler.END
    avail_seats_str = "\n".join([f"Seat {seat['id']}" for seat in avail_seats])
    await update.message.reply_text(f"Available seats on {date}:\n{avail_seats_str}\nPlease enter the seat ID and hour (in 24h format) to book the seat, separated by a space.")
    return ConversationHandler.END

# 3. View existing bookings
async def view_my_bookings(update: Update, context: CallbackContext) -> int:
    if not check_if_logged_on_as_company(update, context):
        await update.message.reply_text("You are not logged in as a company.")
        return ConversationHandler.END
    
    """Displays all existing bookings for the company."""
    data = load_data()
    company_id = context.user_data["company"]["id"]
    # {'company1': [{'date': '2024-02-20', 'hour': '09:00', 'seat_id': 'seat1'}, {'date': '2024-02-20', 'hour': '09:00', 'seat_id': 'seat2'}, 
    # {'date': '2024-02-20', 'hour': '09:00', 'seat_id': 'seat3'}], 'company2': [{'date': '2024-02-20', 'hour': '09:00', 'seat_id': 'seat2'}]}
    # the line below is wrong, what should it be 
    bookings = data["bookings"].get(company_id)
    if not bookings:
        await update.message.reply_text("No existing bookings.")
        return ConversationHandler.END
    bookings_str = "\n".join([f"Seat {booking['seat_id']} on {booking['date']} ({booking['day']}) at {booking['hour']}" for booking in bookings])
    await update.message.reply_text(f"Existing bookings:\n{bookings_str}")
    return ConversationHandler.END