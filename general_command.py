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
        await update.message.reply_text(
            "Admin authenticated. Available commands: /seats, /companies"
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
    text = update.message.text
    # Split the text into company name and password, should be in the form on {company_name}/{password}
    # company_name, password = text.lower().split('/')

    # data[companies] is a list of companies in the form of {
    #   "id": "company2",
    #   "name": "Company2",
    #   "password": "company2"
    # }
    # i want to check if the company name is in the list of companies, regardless of upper or lower case

    if text.lower() in [company["name"].lower() for company in data["companies"]]:
        # context.user_data["company"] should store the corresponding company object
        context.user_data["company"] = [company for company in data["companies"] if company["name"].lower() == text.lower()][0]
        await update.message.reply_text("Please enter your company password:")
        return COMPANY_PASSWORD
    else:
        await update.message.reply_text("Company name not recognized. Please try again.")
        return COMPANY_NAME

async def company_password_check(update: Update, context: CallbackContext) -> int:
    """Checks the company password."""
    company = context.user_data.get("company")
    text = update.message.text
    # data[companies] is a list of companies in the form of [{'id': 'company1', 'name': 'Company1', 'password': 'company1'}, {'id': 'company2', 'name': 'Company2', 'password': 'company2'}]

    if text == company["password"]:
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