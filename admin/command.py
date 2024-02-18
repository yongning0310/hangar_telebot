from telegram.ext import Application, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, filters
from data.data import load_data, save_data
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from datetime import datetime, timedelta

date_format_example = "YYYY-MM-DD"

# put this before every function call below, should raise error if not admin
def check_if_logged_on_as_admin(update: Update, context: CallbackContext) -> bool:
    if context.user_data.get('role') == 'admin':
        return True
    else:
        return False
    
async def cancel_add_company(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Add Company canceled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# 1. Add seats (automatically adds one more seat)
# how to i call check_if_logged_on_as_admin before add_seat?
# i will put this before every function call below, should raise error if not admin
async def add_seat(update: Update, context: CallbackContext) -> int:
    if not check_if_logged_on_as_admin(update, context):
        await update.message.reply_text("You are not logged in as an admin.")
        return ConversationHandler.END

    """Adds a seat to the database."""
    data = load_data()
    seat_id = str(len(data["seats"]) + 1)
    data["seats"][seat_id] = {
        "is_broken": False
    }
    save_data(data)
    await update.message.reply_text(f"Seat {len(data['seats'])} added successfully.")
    return ConversationHandler.END

# 2. Mark seats as broken (by seat_id)
SEAT_ID, SEAT_STATUS = range(2)

async def mark_seat_status(update:Update, context: CallbackContext) -> int:
    # Starts conversation to mark seat as broken
    if not check_if_logged_on_as_admin(update, context):
        await update.message.reply_text("You are not logged in as an admin.")
        return ConversationHandler.END
    await update.message.reply_text("Please enter the seat ID to mark as broken.")
    return SEAT_ID

async def seat_id(update: Update, context: CallbackContext) -> int:
    """Saves seat into context for handling seat status."""
    #assuming seat is 1 indexed
    seat_id = update.message.text
    data = load_data()
    if seat_id not in data["seats"]:
        await update.message.reply_text(f"Seat {seat_id} does not exist. Enter a valid seat id")
        return SEAT_ID
    context.user_data['seat_id'] = seat_id
    await update.message.reply_text("Please enter the physical status of the seat (broken/available)")
    return SEAT_STATUS

async def seat_physical_status(update: Update, context: CallbackContext) -> int:
    """Marks seat as either broken or not broken"""
    #assuming seat is 1 indexed
    data = load_data()
    seat_id = context.user_data['seat_id']
    seat_status = update.message.text
    
    if seat_status == "broken":
        data["seats"][seat_id]["is_broken"] = True
        cancel_booking_by_seat_id(data, seat_id)
    elif seat_status == "available":
        data["seats"][seat_id]["is_broken"] = False
    else:
        await update.message.reply_text("Invalid status. Please enter 'broken' or 'available'.")
        return SEAT_STATUS
    save_data(data)

    await update.message.reply_text(f"Seat {seat_id} marked as {seat_status}.")
    return ConversationHandler.END

async def cancel_booking_by_seat_id(data, seat_id):
    for company_id in data["bookings"]:
        for booking in data["bookings"][company_id]:
            if booking["seat_id"] == seat_id:
                booking["seat_id"] = None
                booking["status"] = "cancelled"
    save_data(data)

mark_seat_handler = ConversationHandler(
    entry_points=[CommandHandler('mark_seat_status', mark_seat_status)],
    states={SEAT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, seat_id)],
            SEAT_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, seat_physical_status)]},
    fallbacks=[CommandHandler('cancel', cancel_add_company)],
)
# 3. View seats avail (by date)
DATE = range(1)
async def view_avail_seats(update: Update, context: CallbackContext) -> int:
    if not check_if_logged_on_as_admin(update, context):
        await update.message.reply_text("You are not logged in as an admin.")
        return ConversationHandler.END
    
    await update.message.reply_text("Please provide date in the format: " + date_format_example)
    return DATE

async def date(update: Update, context: CallbackContext) -> int:
    date_str = update.message.text
    data = load_data()

    # Convert string to datetime object assuming the date format is "YYYY-MM-DD"
    try:
        input_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text("Invalid date format. Please use YYYY-MM-DD.")
        return DATE  # Assuming DATE is a state you've defined for handling date input

    today = datetime.now().date()
    max_date = today + timedelta(days=7)

    # Check if the date is today or within the next 7 days
    if not (today <= input_date.date() <= max_date):
        await update.message.reply_text(f"Date {date_str} is not within 7 days from today. Please enter a valid date.")
        return DATE

    if date_str not in data["dates"]:
        await update.message.reply_text(f"Date {date_str} does not exist. Enter a date that is within 7 days from today")
        return DATE

    all_hours = data["dates"][date_str]
    seats_data = data["seats"]
    await update.message.reply_text(f"Available seats for {date_str}.")

    for hour, seats_dict in all_hours.items():
        available_seats = [
            seat_id for seat_id, seat_info in seats_dict.items()
            if seat_id in seats_data and not seat_info["is_booked"] and not seats_data[seat_id]["is_broken"]
        ]
        available_seats_str = ", ".join(available_seats)
        if available_seats:
            await update.message.reply_text(f"Hour: {hour}, Available seats: {available_seats_str}")
        else:
            await update.message.reply_text(f"Hour: {hour}, No available seats.")
    return ConversationHandler.END


async def cancel_view_avail_seats(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('View Available Seats canceled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

view_avail_seats_handler = ConversationHandler(
    entry_points=[CommandHandler('view_avail_seats', view_avail_seats)],
    states={DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, date)]},
    fallbacks=[CommandHandler('cancel', cancel_view_avail_seats)],
)

# 4. Add company (name, password, quota) (prevent duplicate names)
# Define states
COMPANY_NAME, COMPANY_PASSWORD, COMPANY_QUOTA = range(3)

async def add_company(update: Update, context: CallbackContext) -> int:
    if not check_if_logged_on_as_admin(update, context):
        await update.message.reply_text("You are not logged in as an admin.")
        return ConversationHandler.END
    
    """Starts the conversation to add a new company."""
    context.user_data['company_id'] = str(len(load_data()["companies"]) + 1)
    await update.message.reply_text("Please enter the name for the new company:")
    return COMPANY_NAME

def add_company_and_quota_to_database(company_id, company_name, company_password, company_quota):
    data = load_data()
    data["companies"][company_id] = {
        "id": company_id,
        "name": company_name,
        "password": company_password
    }
    data["quotas"][company_id] = {
        "total_quota": company_quota,
        "quota_used": 0
    }
    save_data(data)

async def company_name(update: Update, context: CallbackContext) -> int:
    """Stores the company name and asks for the password."""
    company_name = update.message.text
    if company_name in load_data()["companies"]:
        await update.message.reply_text("Company name already exists. Please enter a different name.")
        return COMPANY_NAME
    context.user_data['company_name'] = update.message.text

    await update.message.reply_text("Please enter the company password:")
    return COMPANY_PASSWORD

async def company_password(update: Update, context: CallbackContext) -> int:
    """Stores the company password and asks for the quota."""
    context.user_data['company_password'] = update.message.text
    await update.message.reply_text("Please enter the company quota:")
    return COMPANY_QUOTA

async def company_quota(update: Update, context: CallbackContext) -> int:
    """Stores the company quota and ends the conversation."""
    context.user_data['company_quota'] = update.message.text
    data = load_data()
    # Add the company to the database
    # This is a placeholder, replace it with your actual database logic
    company_id = context.user_data['company_id']
    company_name = context.user_data['company_name']
    company_password = context.user_data['company_password']
    company_quota = context.user_data['company_quota']

    add_company_and_quota_to_database(company_id, company_name, company_password, company_quota)

    await update.message.reply_text("Company added successfully!")
    return ConversationHandler.END



add_company_handler = ConversationHandler(
    entry_points=[CommandHandler('add_company', add_company)],
    states={
        COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_name)],
        COMPANY_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_password)],
        COMPANY_QUOTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_quota)]
    },
    fallbacks=[CommandHandler('cancel', cancel_add_company)],
)

# 5. Delete company (by company id)
DEL_COMPANY_ID = range(1)
async def delete_company(update: Update, context: CallbackContext) -> None:
    if not check_if_logged_on_as_admin(update, context):
        await update.message.reply_text("You are not logged in as an admin.")
        return ConversationHandler.END
    
    """Starts delete conversation."""
    await update.message.reply_text("Please enter the id of the company to delete:")
    return DEL_COMPANY_ID

async def delete_company_id(update: Update, context: CallbackContext) -> int:
    """Deletes the company id if valid"""
    company_id = update.message.text

    # Load data
    data = load_data()

    if company_id not in data["companies"]:
        await update.message.reply_text(f"Company {company_id} does not exist. Enter a valid company id.")
        return DEL_COMPANY_ID

    # should remove company from json and save to database
    # remove from data["companies"]
    #delete from data["bookings"]


    del data["companies"][company_id]
    del data["quotas"][company_id]
    del data["bookings"][company_id]

    save_data(data)
    context.user_data['company_id'] = company_id
    await update.message.reply_text("Deleted successfully.")
    return ConversationHandler.END

async def cancel_delete_company(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Delete Company canceled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Define the conversation handler
delete_company_handler = ConversationHandler(
    entry_points=[CommandHandler('delete_company', delete_company)],
    states={
        DEL_COMPANY_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_company_id)],
    },
    fallbacks=[CommandHandler('cancel', cancel_delete_company)],  # You would need to define a 'cancel' function
)



# 6. Edit company (by company id, edit quota/password)
# Define states
COMPANY_ID, EDIT_FIELD, EDIT_NAME, EDIT_PASSWORD, EDIT_QUOTA = range(5)
async def edit_company(update: Update, context: CallbackContext) -> int:
    if not check_if_logged_on_as_admin(update, context):
        await update.message.reply_text("You are not logged in as an admin.")
        return ConversationHandler.END
    
    """Starts the conversation to edit a company."""
    await update.message.reply_text("Please enter the id of the company to edit:")
    return COMPANY_ID

async def company_id(update: Update, context: CallbackContext) -> int:
    """Stores the company id and asks what field to edit."""
    company_id = update.message.text

    # Load data
    data = load_data()
    print( data["companies"])
    if company_id not in data["companies"]:
        await update.message.reply_text(f"Company {company_id} does not exist.")
        return ConversationHandler.END

    context.user_data['company_id'] = company_id
    await update.message.reply_text("Enter 'name' to edit name, 'password' to edit password, 'quota' to edit quota:")
    return EDIT_FIELD

async def edit_field(update: Update, context: CallbackContext) -> int:
    """Determines what field to edit based on user input or ends the conversation."""
    text = update.message.text.lower()
    if text == 'yes':
        await update.message.reply_text("Enter 'name' to edit name, 'password' to edit password, 'quota' to edit quota:")
        return EDIT_FIELD
    elif text == 'no':
        await update.message.reply_text("Editing ended.")
        return ConversationHandler.END
    elif text == 'name':
        await update.message.reply_text("Please enter the new company name:")
        return EDIT_NAME
    elif text == 'password':
        await update.message.reply_text("Please enter the new company password:")
        return EDIT_PASSWORD
    elif text == 'quota':
        await update.message.reply_text("Please enter the new company quota:")
        return EDIT_QUOTA
    else:
        await update.message.reply_text("Invalid input. Please enter 'name', 'password', 'quota', 'yes', or 'no'.")
        return EDIT_FIELD
    
async def edit_name(update: Update, context: CallbackContext) -> int:
    """Edits the company name."""
    # Here you would typically edit the company name in your database
    data =  load_data()
    company_id = context.user_data['company_id']
    data["companies"][company_id]['name'] = update.message.text
    save_data(data)

    await update.message.reply_text("Company name edited successfully! Do you want to continue editing? (yes/no)")
    return EDIT_FIELD

async def edit_password(update: Update, context: CallbackContext) -> int:
    """Edits the company password."""
    data =  load_data()
    company_id = context.user_data['company_id']
    data["companies"][company_id]['password'] = update.message.text
    save_data(data)

    await update.message.reply_text("Company password edited successfully! Do you want to continue editing? (yes/no)")
    return EDIT_FIELD

async def edit_quota(update: Update, context: CallbackContext) -> int:
    """Edits the company quota."""
    data =  load_data()
    company_id = context.user_data['company_id']
    data["quotas"][company_id]['total_quota'] = int(update.message.text)
    save_data(data)
    # Here you would typically edit the company quota in your database
    await update.message.reply_text("Company quota edited successfully! Do you want to continue editing? (yes/no)")
    return EDIT_FIELD

async def cancel_edit_company(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Edit Company canceled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# Define the conversation handler
edit_company_handler = ConversationHandler(
    entry_points=[CommandHandler('edit_company', edit_company)],
    states={
        COMPANY_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_id)],
        EDIT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field)],
        EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_name)],
        EDIT_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_password)],
        EDIT_QUOTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_quota)]
    },
    fallbacks=[CommandHandler('cancel', cancel_edit_company)],  # You would need to define a 'cancel' function
)


#7. View all companies (total quota, current quota used, company name, company password)
#might make password not visible since privacy concern
async def view_all_companies(update: Update, context: CallbackContext) -> None:
    if not check_if_logged_on_as_admin(update, context):
        await update.message.reply_text("You are not logged in as an admin.")
        return ConversationHandler.END
    
    """Displays information about all companies."""
    data = load_data()
    await update.message.reply_text("All companies:")
    for company_id in data["companies"]:
        company = data["companies"][company_id]
        company_quota = data["quotas"][company_id]
        await update.message.reply_text(f"ID:{company['id']}, Name: {company['name']}, Password: {company['password']}, Total quota: {company_quota['total_quota']}, Quota used: {company_quota['quota_used']}")

async def view_all_seats(update: Update, context: CallbackContext) -> None:
    if not check_if_logged_on_as_admin(update, context):
        await update.message.reply_text("You are not logged in as an admin.")
        return ConversationHandler.END
    
    """Displays information about all seats."""
    data = load_data()
    for seat_id in data["seats"]:
        seat = data["seats"][seat_id]
        await update.message.reply_text(f"Seat ID: {seat_id}, Is broken: {seat['is_broken']}")

#8. View a specific company (by company id)
async def view_company(update: Update, context: CallbackContext) -> None:
    if not check_if_logged_on_as_admin(update, context):
        await update.message.reply_text("You are not logged in as an admin.")
        return ConversationHandler.END
    
    """Displays information about a specific company."""
    if not context.args:
        await update.message.reply_text("No company ID provided.")
        return
    company_id = context.args[0]
    data = load_data()
    if company_id not in data["companies"]:
        await update.message.reply_text(f"Company {company_id} does not exist.")
        return
    company = data["companies"][company_id]
    await update.message.reply_text(f"Name: {company['name']}, Password: {company['password']}, Quota: {company['quota']}")