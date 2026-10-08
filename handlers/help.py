from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from keyboards import help_menu


async def help_center(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📚 *Nebumine pro Help Center*\n\n"
        "Select an option below.",
        parse_mode="Markdown",
        reply_markup=help_menu,
    )


help_handler = MessageHandler(
    filters.Regex("^ℹ️ Help$"),
    help_center,
)
