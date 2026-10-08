from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)

from config import ADMIN_ID
from database import get_support_user


async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Only allow admin
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return

    replied_message_id = update.message.reply_to_message.message_id

    user_id = get_support_user(replied_message_id)

    if not user_id:

       await update.message.reply_text(
        "❌ Unable to identify the user."
       )

       return

    # ---------- TEXT ----------
    if update.message.text:

        await context.bot.send_message(
            chat_id=user_id,
            text=f"💬 *Support Reply*\n\n{update.message.text}",
            parse_mode="Markdown",
        )

    # ---------- PHOTO ----------
    elif update.message.photo:

        photo = update.message.photo[-1].file_id

        caption = update.message.caption or ""

        await context.bot.send_photo(
            chat_id=user_id,
            photo=photo,
            caption=f"💬 Support Reply\n\n{caption}",
        )

    else:

        await update.message.reply_text(
            "❌ Only text messages and photos can be sent."
        )

        return

    await update.message.reply_text("✅ Reply delivered successfully.")


reply_handler = MessageHandler(
    filters.REPLY & (filters.TEXT | filters.PHOTO),
    reply_to_user,
    )
