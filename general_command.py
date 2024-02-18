from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext
from data.data import load_data, save_data

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

