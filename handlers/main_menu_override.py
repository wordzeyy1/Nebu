from telegram.ext import ConversationHandler
from keyboards import main_menu

async def main_menu_override(update, context):

    context.user_data.clear()

    await update.message.reply_text(
        "🏠 Main Menu",
        reply_markup=main_menu,
    )

    return ConversationHandler.END
