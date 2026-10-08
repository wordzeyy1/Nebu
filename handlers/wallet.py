from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from keyboards import wallet_menu
from database import get_user

# Navigation
from handlers.navigation import push_page


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Save current page in navigation stack
    if not context.user_data.get("from_back", False):
        push_page(context, "wallet")
    
    print("========== NAVIGATION STACK ==========")
    print(context.user_data.get("navigation_stack"))
    print("======================================")

    user_id = update.effective_user.id

    print("Telegram User ID:", update.effective_user.id)

    user = get_user(user_id)

    print("Database result:", user)
    print("Wallet User ID:", user_id)
    print("Database User:", user)

    if user is None:
        await update.message.reply_text(
            "❌ Please register first."
        )
        return

    message = f"""
💼 *NEBUMINE PRO WALLET*

━━━━━━━━━━━━━━

💰 Wallet Balance: ${user[7]:.2f}

💵 Affiliate Balance: ${user[8]:.2f}

━━━━━━━━━━━━━━

Choose an option below.
"""

    await update.message.reply_text(
        message,
        reply_markup=wallet_menu,
        parse_mode="Markdown",
    )


wallet_handler = MessageHandler(
    filters.Regex("^💼 Wallet$"),
    wallet,
    )
