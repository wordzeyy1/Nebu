from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from keyboards import main_menu, admin_menu
from config import ADMIN_ID


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🏠 Returned to the Main Menu.",
        reply_markup=(
            admin_menu
            if update.effective_user.id == ADMIN_ID
            else main_menu
        ),
    )

    return ConversationHandler.END
