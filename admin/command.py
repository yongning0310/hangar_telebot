from telegram.ext import Application, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, filters
from data.data import load_data, save_data
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from general_command import cancel

date_format_example = "YYYY-MM-DD"

# 1. Add seats (automatically adds one more seat)
async def add_seat(update: Update, context: CallbackContext) -> int:
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
async def mark_seat_as_broken(update:Update, context: CallbackContext) -> int:
    """Marks a seat as broken."""
    #assuming seat is 1 indexed
    data = load_data()
    if not context.args:
        await update.message.reply_text("No seat ID provided.")
        return ConversationHandler.END

    seat_id = context.args[0]
    if seat_id not in data["seats"]:
        await update.message.reply_text(f"Seat {seat_id} does not exist.")
        return ConversationHandler.END
    
    data["seats"][seat_id]["is_broken"] = True
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
    company_name = update.message.text
    data = load_data()
    # Check if the company name already exists in the database
    # This is a placeholder, replace it with your actual database logic
    if company_name in data["companies"]:
        await update.message.reply_text("A company with this name already exists. Please try again with a different name.")
        return ConversationHandler.END

    await update.message.reply_text("Please enter the password for the new company:")
    context.user_data['company_name'] = company_name
    return COMPANY_PASSWORD

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

    # Add the company to the database
    # This is a placeholder, replace it with your actual database logic
    company_id = context.user_data['company_id']
    company_name = context.user_data['company_name']
    company_password = context.user_data['company_password']
    company_quota = context.user_data['company_quota']
    add_company_to_database(company_id, company_name, company_password, company_quota)

    await update.message.reply_text("Company added successfully!")
    return ConversationHandler.END

async def add_company_to_database(company_id, company_name, company_password, company_quota):
    data = load_data()

    num_companies = len(data["companies"])
    data["companies"][num_companies + 1] = {
        
        "name": company_name,
        "password": company_password,
        "quota": company_quota
    }
    save_data(data)

add_company_handler = ConversationHandler(
    entry_points=[CommandHandler('add_company', add_company)],
    states={
        COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_name)],
        COMPANY_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_password)],
        COMPANY_QUOTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_quota)]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

# 5. Delete company (by company id)
async def delete_company(update: Update, context: CallbackContext) -> None:
    """Deletes a company from the database."""
    if not context.args:
        await update.message.reply_text("No company ID provided.")
        return
    
    company_id = context.args[0]
    data = load_data()
    if company_id not in data["companies"]:
        await update.message.reply_text(f"Company {company_id} does not exist.")
        return
    
    del data["companies"][company_id]
    save_data(data)
    await update.message.reply_text(f"Company {company_id} deleted successfully.")

# 6. Edit company (by company id, edit quota/password)
# Define states
COMPANY_ID, EDIT_FIELD, EDIT_NAME, EDIT_PASSWORD, EDIT_QUOTA = range(5)
async def edit_company(update: Update, context: CallbackContext) -> int:
    """Starts the conversation to edit a company."""
    await update.message.reply_text("Please enter the id of the company to edit:")
    return COMPANY_ID

async def company_id(update: Update, context: CallbackContext) -> int:
    """Stores the company id and asks what field to edit."""
    company_id = update.message.text

    # Load data
    data = load_data()
    num_companies = len(data["companies"])
    if company_id < 1 or company_id > num_companies or company_id not in data["companies"]:
        await update.message.reply_text(f"Company {company_id} does not exist.")
        return ConversationHandler.END
    # Store the data in context.user_data
    context.user_data['company_data'] = data

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
    company_id = context.user_data['company_id']

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
async def view_all_companies(update: Update, context: CallbackContext) -> None:
    """Displays information about all companies."""
    data = load_data()
    for company in data["companies"]:
        await update.message.reply_text(f"Name: {company['name']}, Password: {company['password']}, Quota: {company['quota']}")

#view info of a particular company
async def view_company(update: Update, context: CallbackContext) -> None:
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