from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from keyboards import fund_keyboard

# Navigation
from handlers.navigation import push_page


async def fund_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Save current page
    if not context.user_data.get("from_back", False):
        push_page(context, "fund_wallet")
    # Debug navigation stack
    print("========== NAVIGATION STACK ==========")
    print(context.user_data.get("navigation_stack"))
    print("======================================")

    await update.message.reply_text(
        "💳 *Fund Wallet*\n\n"
        "Select the cryptocurrency you want to deposit:",
        reply_markup=fund_keyboard,
        parse_mode="Markdown"
    )


fund_wallet_handler = MessageHandler(
    filters.Regex("^📥 Fund Wallet$"),
    fund_wallet,
)
