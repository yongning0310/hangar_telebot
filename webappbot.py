#!/usr/bin/env python
import json
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Utility Functions
def load_data():
    with open("data/database.json", "r") as file:
        return json.load(file)

def save_data(data):
    with open("data/database.json", "w") as file:
        json.dump(data, file, indent=4)

# Command Handlers
async def start(update: Update, context: CallbackContext) -> None:
    """Starts the bot and displays available commands."""
    await update.message.reply_text(
        "Welcome! Use /admin for admin actions or /company for company actions.",
    )

async def admin_login(update: Update, context: CallbackContext) -> None:
    """Prompts for admin password."""
    await update.message.reply_text("Please enter the admin password:", reply_markup=ReplyKeyboardRemove())

async def company_login(update: Update, context: CallbackContext) -> None:
    """Prompts for company name."""
    await update.message.reply_text("Please enter your company name:", reply_markup=ReplyKeyboardRemove())

# Message Handlers
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    data = load_data()
    
    if text == data["admin_password"]:
        await update.message.reply_text("Admin authenticated. Available commands: /add_company, /edit_quota, /delete_company")
    elif text in data["companies"]:
        context.user_data["company_name"] = text
        await update.message.reply_text("Please enter your company password:")
    elif "company_name" in context.user_data and text == data["companies"][context.user_data["company_name"]]["password"]:
        await update.message.reply_text(f"Authenticated as {context.user_data['company_name']}. Use /book_seat to book a seat.")
    else:
        await update.message.reply_text("Invalid credentials or command.")

# Define states for conversation
COMPANY_NAME, COMPANY_QUOTA, COMPANY_PASSWORD = range(3)

async def add_company(update: Update, context: CallbackContext) -> int:
    """Starts the conversation to add a new company."""
    await update.message.reply_text("Please enter the name of the new company:")
    return COMPANY_NAME

async def company_name(update: Update, context: CallbackContext) -> int:
    """Stores the company name and asks for the quota."""
    context.user_data['company_name'] = update.message.text
    await update.message.reply_text("Please enter the quota for the new company:")
    return COMPANY_QUOTA

async def company_quota(update: Update, context: CallbackContext) -> int:
    """Stores the company quota and asks for the password."""
    context.user_data['company_quota'] = update.message.text
    await update.message.reply_text("Please enter the password for the new company:")
    return COMPANY_PASSWORD

async def company_password(update: Update, context: CallbackContext) -> int:
    """Stores the company password and adds the company to the database."""
    context.user_data['company_password'] = update.message.text
    # Now, you have all data needed to add the company. Insert the logic to update the JSON file here.
    data = load_data()  # Assume load_data loads your JSON file
    company_name = context.user_data['company_name']
    data['companies'][company_name] = {
        "password": context.user_data['company_password'],
        "quota": int(context.user_data['company_quota']),
        "seats_booked": []
    }
    save_data(data)  # Assume save_data writes to your JSON file
    await update.message.reply_text(f"Company {company_name} added successfully.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def edit_quota(update: Update, context: CallbackContext) -> None:
    # Ensure there are at least 2 arguments (command, name, and either quota or password)
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /edit_quota <name> <quota/password> <new value>")
        return
    
    company_name, attribute, new_value = context.args[0], context.args[1], context.args[2]

    # Load current database
    data = load_data()
    
    # Check if company exists
    if company_name not in data["companies"]:
        await update.message.reply_text(f"Company {company_name} does not exist.")
        return
    
    # Edit quota or password
    if attribute.lower() == "quota":
        data["companies"][company_name]["quota"] = int(new_value)
    elif attribute.lower() == "password":
        data["companies"][company_name]["password"] = new_value
    else:
        await update.message.reply_text("Invalid attribute. Use 'quota' or 'password'.")
        return

    # Save updated database
    save_data(data)
    
    await update.message.reply_text(f"{company_name}'s {attribute} updated successfully.")

async def delete_company(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /delete_company <name>")
        return
    
    company_name = context.args[0]

    # Load current database
    data = load_data()

    # Check if company exists
    if company_name not in data["companies"]:
        await update.message.reply_text(f"Company {company_name} does not exist.")
        return
    
    # Delete company
    del data["companies"][company_name]

    # Save updated database
    save_data(data)

    await update.message.reply_text(f"Company {company_name} deleted successfully.")


async def book_seat(update: Update, context: CallbackContext) -> None:
    # This function would allow a company to book a seat
    pass

def main():
    application = Application.builder().token("TOKEN").build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_login))
    application.add_handler(CommandHandler("company", company_login))

    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Placeholder handlers for admin and company commands
    application.add_handler(CommandHandler("add_company", add_company))
    application.add_handler(CommandHandler("edit_quota", edit_quota))
    application.add_handler(CommandHandler("book_seat", book_seat))

    application.run_polling()

if __name__ == "__main__":
    main()




