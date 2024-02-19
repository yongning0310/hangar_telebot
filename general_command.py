from error_handler import handle_errors
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext, ConversationHandler
from data.data import load_data

# Define states for each conversation
ADMIN_PASSWORD = range(1)
data = load_data()
ENTER_COMPANY_NAME_AGAIN = "Please enter your company name again."
ENTER_PASSWORD_AGAIN = "Please enter your password again."

# @handle_errors
async def logout(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()  # Clear user-specific data
    await update.message.reply_text("You have been logged out.")
    return ConversationHandler.END

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
    if text == data['admin']['password']:  # Replace with your actual admin password
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
            "/view_all_bookings - View company details (For Admin).\n"
            "/view_all_seats - List all seats (For Admin)."
        )


        context.user_data['role'] = 'admin'
        return ConversationHandler.END
    else:
        await update.message.reply_text("Incorrect password. " + ENTER_PASSWORD_AGAIN)
        return ADMIN_PASSWORD
    
# Define conversation handler for admin login
admin_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('admin', admin_login)],
    states={
        ADMIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_password_check)],
    },
    fallbacks=[CommandHandler('restart', logout)]
)

##############################################################################################################################################################################

GENERAL_COMPANY_NAME, COMPANY_PASSWORD = range(2)
# Company Handlers
async def company_login(update: Update, context: CallbackContext) -> int:
    """Prompts for company name."""
    await update.message.reply_text("Please enter your company name:")
    return GENERAL_COMPANY_NAME

# @handle_errors
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
        await update.message.reply_text("Company name not recognized. " + ENTER_COMPANY_NAME_AGAIN)
        return GENERAL_COMPANY_NAME
    
def is_valid_company_name(company_name: str) -> bool:
    #checks that name exists in the list of companies
    data = load_data()
    return company_name.lower() in [data["companies"][company_id]["name"].lower() for company_id in data["companies"]]

# @handle_errors
async def company_password_check(update: Update, context: CallbackContext) -> int:
    """Checks the company password."""
    company = context.user_data["company"]
    input_password = update.message.text

    if input_password == company["password"]:
        company_name = company["name"]
        await update.message.reply_text(
            f"Company authenticated as {company_name}. Available commands:\n"
            "/check_quota - Check Total and Used quota (For Company).\n"
            "/view_avail_seats - View available seats (For Company).\n"
            "/book_seats - Book seats (For Company).\n"
            "/view_my_bookings - View existing bookings (For Company).\n"
        )
        
        context.user_data['role'] = 'company'
        return ConversationHandler.END
    else:
        await update.message.reply_text("Incorrect password. " + ENTER_PASSWORD_AGAIN)
        return COMPANY_PASSWORD


# Define conversation handler for company login
company_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('company', company_login)],
    states={
        GENERAL_COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_name_check)],
        COMPANY_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_password_check)],
    },
    fallbacks=[CommandHandler('restart', logout)]
)