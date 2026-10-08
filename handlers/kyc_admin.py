from telegram import Update

from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from config import ADMIN_ID
from database import update_kyc_status


# ==========================================
# APPROVE KYC
# ==========================================

async def approve_kyc(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 1:

        await update.message.reply_text(
            "Usage:\n/approve_kyc <user_id>"
        )
        return

    user_id = int(context.args[0])

    update_kyc_status(
        user_id,
        "Approved",
    )

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "🎉 *KYC Approved!*\n\n"
            "Congratulations!\n\n"
            "Your KYC verification has been approved.\n"
            "You now have full access to Nebumine pro."
        ),
        parse_mode="Markdown",
    )

    await update.message.reply_text(
        "✅ KYC approved successfully."
    )


# ==========================================
# HANDLER
# ==========================================

approve_kyc_handler = CommandHandler(
    "approve_kyc",
    approve_kyc,
)

# ==========================================
# REJECT KYC
# ==========================================

async def reject_kyc(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 1:

        await update.message.reply_text(
            "Usage:\n/reject_kyc <user_id>"
        )
        return

    user_id = int(context.args[0])

    update_kyc_status(
        user_id,
        "Rejected",
    )

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "❌ *KYC Rejected*\n\n"
            "Unfortunately, your KYC verification "
            "could not be approved.\n\n"
            "Please submit a clearer government-issued "
            "ID and a clear selfie holding the ID."
        ),
        parse_mode="Markdown",
    )

    await update.message.reply_text(
        "❌ KYC rejected successfully."
    )


# ==========================================
# HANDLER
# ==========================================

reject_kyc_handler = CommandHandler(
    "reject_kyc",
    reject_kyc,
)

# ==========================================
# INLINE APPROVE / REJECT CALLBACK
# ==========================================

async def kyc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    print("CALLBACK RECEIVED")

    query = update.callback_query
    await query.answer()

    print(query.data)

    if update.effective_user.id != ADMIN_ID:
        return

    action, user_id = query.data.split(":")
    user_id = int(user_id)

    if action == "approve_kyc":

        update_kyc_status(user_id, "Approved")

        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Your KYC has been approved.",
        )

        await query.edit_message_caption(
            caption="✅ KYC Approved"
        )

    elif action == "reject_kyc":

        update_kyc_status(user_id, "Rejected")

        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Your KYC was rejected.",
        )

        await query.edit_message_caption(
            caption="❌ KYC Rejected"
        )


kyc_callback_handler = CallbackQueryHandler(
    kyc_callback,
    pattern="^(approve_kyc|reject_kyc):",
      )
