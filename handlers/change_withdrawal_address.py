from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from database import (
    get_user,
    update_wallet_address,
)

ADDRESS = 0


async def change_withdrawal_address(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = get_user(update.effective_user.id)

    current = user[5] if user[5] else "Not Set"

    await update.message.reply_text(
        "🏦 *Default Withdrawal Address*\n\n"
        f"Current Address:\n\n"
        f"`{current}`\n\n"
        "Send your new withdrawal address.",
        parse_mode="Markdown",
    )

    return ADDRESS


async def save_withdrawal_address(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    address = update.message.text.strip()

    update_wallet_address(
        update.effective_user.id,
        address,
    )

    await update.message.reply_text(
        "✅ Default withdrawal address updated successfully."
    )

    return ConversationHandler.END


change_withdrawal_address_handler = ConversationHandler(

    entry_points=[
        MessageHandler(
            filters.Regex("^🏦 Change Withdrawal Address$"),
            change_withdrawal_address,
        )
    ],

    states={
        ADDRESS: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                save_withdrawal_address,
            )
        ]
    },

    fallbacks=[],
)
