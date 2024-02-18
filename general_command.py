from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext, ConversationHandler
from data.data import load_data

# Define states for each conversation
ADMIN_PASSWORD, COMPANY_NAME, COMPANY_PASSWORD = range(3)
data = load_data()

# Command Handlers
async def start(update: Update, context: CallbackContext) -> None:
    """Starts the bot and displays available commands."""
    await update.message.reply_text(
        "Welcome! Use /admin for admin actions or /company for company actions.",
    )

# Admin Handlers
async def admin_login(update: Update, context: CallbackContext) -> int:
    """Prompts for admin password."""
    await update.message.reply_text(
        "Please enter the admin password:",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADMIN_PASSWORD

async def admin_password_check(update: Update, context: CallbackContext) -> int:
    """Checks the admin password."""
    text = update.message.text
    if text == data['admin'][0]['password']:  # Replace with your actual admin password
        #how to have a multi-line message?

        await update.message.reply_text(
            "Admin authenticated. Available commands:\n"
            "/add_seat - Add seat (For Admin).\n"
            "/mark_seat_status - Mark seat as broken/ available (For Admin).\n"
            "/view_avail_seats - View available seats (For Admin).\n"
            "/edit_company - Edit a company (For Admin).\n"
            "/add_company - Add a new company (For Admin).\n"
            "/delete_company - Delete a company (For Admin).\n"
            "/view_all_companies - List all companies (For Admin).\n"
            "/view_company - View company details (For Admin).\n"
            "/view_all_seats - List all seats (For Admin)."
        )

        context.user_data['role'] = 'admin'
        return ConversationHandler.END
    else:
        await update.message.reply_text("Incorrect password. Please try again.")
        return ADMIN_PASSWORD

# Company Handlers
async def company_login(update: Update, context: CallbackContext) -> int:
    """Prompts for company name."""
    await update.message.reply_text("Please enter your company name:")
    return COMPANY_NAME

async def company_name_check(update: Update, context: CallbackContext) -> int:
    """Checks the company name and prompts for password."""
    input_company_name = update.message.text
    # Check if the company name is in the list of companies (case-insensitive)

    # print(data["companies"])
    if is_valid_company_name(input_company_name):
        #should only have one company that is a match, thus use "next"
        company_list = [data["companies"][company_id] for company_id in data["companies"]]
        context.user_data["company"] = next(company for company in company_list if company["name"].lower() == input_company_name.lower())

        await update.message.reply_text("Please enter your company password:")
        return COMPANY_PASSWORD
    else:
        await update.message.reply_text("Company name not recognized. Please try again.")
        return COMPANY_NAME
    
async def is_valid_company_name(company_name: str) -> bool:
    data = load_data()
    return company_name.lower() in [data["companies"][company_id]["name"].lower() for company_id in data["companies"]]

async def company_password_check(update: Update, context: CallbackContext) -> int:
    """Checks the company password."""
    company = context.user_data["company"]
    input_password = update.message.text

    if input_password == company["password"]:
        company_name = company["name"]
        await update.message.reply_text(f"Authenticated as {company_name}")
        context.user_data['role'] = 'company'
        return ConversationHandler.END
    else:
        await update.message.reply_text("Incorrect password. Please try again.")
        return COMPANY_PASSWORD

async def logout(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()  # Clear user-specific data
    await update.message.reply_text("You have been logged out.")