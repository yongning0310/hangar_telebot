from telegram.ext import Application, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, filters
from data.data import load_data, save_data
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from general_command import cancel

date_format_example = "YYYY-MM-DD"

# i will put this before every function call below, should raise error if not admin
def check_if_logged_on_as_admin(update: Update, context: CallbackContext) -> bool:
    if context.user_data.get('role') == 'admin':
        return True
    else:
        return False


# 1. Add seats (automatically adds one more seat)
# how to i call check_if_logged_on_as_admin before add_seat?
# i will put this before every function call below, should raise error if not admin
async def add_seat(update: Update, context: CallbackContext) -> int:
    if not check_if_logged_on_as_admin(update, context):
        await update.message.reply_text("You are not logged in as an admin.")
        return ConversationHandler.END

    """Adds a seat to the database."""
    data = load_data()
    data["seats"].append({
        "id": len(data["seats"]) + 1,
        "is_broken": False
    })
    save_data(data)
    await update.message.reply_text(f"Seat {len(data['seats'])} added successfully.")
    return ConversationHandler.END

# 2. Mark seats as broken (by seat_id)
async def mark_seat_as_broken(update:Update, context: CallbackContext) -> int:
    """Marks a seat as broken."""
    #assuming seat is 1 indexed
    data = load_data()
    if not context.args:
        await update.message.reply_text("No seat ID provided.")
        return ConversationHandler.END

    seat_id = int(context.args[0])
    if seat_id < 1 or seat_id > len(data["seats"]):
        await update.message.reply_text(f"Seat {seat_id} does not exist.")
        return ConversationHandler.END
    
    data["seats"][seat_id - 1]["is_broken"] = True
    save_data(data)
    await update.message.reply_text(f"Seat {seat_id} marked as broken.")
    return ConversationHandler.END

# 3. View seats avail (by date)
async def view_avail_seats(update: Update, context: CallbackContext) -> int:
    """Displays all available seats for a given date."""
    data = load_data()
    if not context.args:
        await update.message.reply_text("Please provide date in the format: " + date_format_example)
        return ConversationHandler.END
    date = context.args[0]

    if date not in data["dates"]:
        await update.message.reply_text(f"No data available for {date}.")
        return ConversationHandler.END
    
    all_hours = data["dates"][date]
    await update.message.reply_text("Available seats for the given date.")

    for hour in all_hours:
        await update.message.reply_text(f"Hour: {hour['hour']}, Available seats: {hour['available_seats']}")
    
    return ConversationHandler.END

# 4. Add company (name, password, quota) (prevent duplicate names)
# Define states
COMPANY_NAME, COMPANY_PASSWORD, COMPANY_QUOTA = range(3)

async def add_company(update: Update, context: CallbackContext) -> int:
    """Starts the conversation to add a new company."""
    await update.message.reply_text("Please enter the name of the new company:")
    return COMPANY_NAME

async def company_name(update: Update, context: CallbackContext) -> int:
    """Stores the company name and asks for the password."""
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
    await update.message.reply_text("Company added successfully!")
    # Here you would typically add the company to your database
    return ConversationHandler.END

# 5. Delete company (by company id)
async def delete_company(update: Update, context: CallbackContext) -> None:
    """Deletes a company from the database."""
    if not context.args:
        await update.message.reply_text("No company name provided.")
        return
    
    company_name = context.args[0]
    data = load_data()
    if company_name not in data["companies"]:
        await update.message.reply_text(f"Company {company_name} does not exist.")
        return
    
    del data["companies"][company_name]
    save_data(data)
    await update.message.reply_text(f"Company {company_name} deleted successfully.")

# 6. Edit company (by company id, edit quota/password)
# Define states
COMPANY_ID, EDIT_FIELD, EDIT_NAME, EDIT_PASSWORD, EDIT_QUOTA = range(5)
async def edit_company(update: Update, context: CallbackContext) -> int:
    """Starts the conversation to edit a company."""
    await update.message.reply_text("Please enter the id of the company to edit:")
    return COMPANY_ID

async def company_id(update: Update, context: CallbackContext) -> int:
    """Stores the company id and asks what field to edit."""
    context.user_data['company_id'] = update.message.text
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
    await update.message.reply_text("Company name edited successfully! Do you want to continue editing? (yes/no)")
    return EDIT_FIELD

async def edit_password(update: Update, context: CallbackContext) -> int:
    """Edits the company password."""
    # Here you would typically edit the company password in your database
    await update.message.reply_text("Company password edited successfully! Do you want to continue editing? (yes/no)")
    return EDIT_FIELD

async def edit_quota(update: Update, context: CallbackContext) -> int:
    """Edits the company quota."""
    # Here you would typically edit the company quota in your database
    await update.message.reply_text("Company quota edited successfully! Do you want to continue editing? (yes/no)")
    return EDIT_FIELD

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
    fallbacks=[CommandHandler('cancel', cancel)],  # You would need to define a 'cancel' function
)

#view companies (total quota, current quota used, company name, company password)

