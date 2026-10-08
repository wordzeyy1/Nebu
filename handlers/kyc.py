from telegram import (
    Update,
    ReplyKeyboardMarkup,
)

from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import ADMIN_ID

from database import (
    submit_kyc as save_kyc,
    get_kyc,
    get_kyc_status,
    update_kyc_status,
)

from keyboards import (
    main_menu,
    admin_menu,
    cancel_menu,
)

# ==========================================
# STATES
# ==========================================

FULL_NAME = 0
ID_DOCUMENT = 1
SELFIE = 2

# ==========================================
# KEYBOARDS
# ==========================================

cancel_menu = ReplyKeyboardMarkup(
    [
        ["❌ Cancel"],
    ],
    resize_keyboard=True,
)

done_keyboard = ReplyKeyboardMarkup(
    [
        ["❌ Cancel"],
    ],
    resize_keyboard=True,
)

# ==========================================
# START KYC
# ==========================================

async def submit_kyc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_kyc_status(update.effective_user.id)

    if status == "Pending":
        await update.message.reply_text(
            "🪪 Your KYC is already under review.\n\n"
            "Please wait for our Compliance Team to complete verification.",
            reply_markup=main_menu,
        )
        return ConversationHandler.END

    if status == "Approved":
        await update.message.reply_text(
            "✅ Your KYC has already been approved.\n\n"
            "There is no need to submit another verification.",
            reply_markup=main_menu,
        )
        return ConversationHandler.END

    # Clear only previous KYC conversation data
    context.user_data.pop("full_name", None)
    context.user_data.pop("id_document", None)
    context.user_data.pop("selfie_document", None)

    await update.message.reply_text(
        "🪪 *Know Your Customer (KYC) Verification*\n\n"
        "*Step 1 of 3*\n\n"
        "Please enter your *Full Name* exactly as it appears on:\n\n"
        "• Your Nebumine pro registration\n"
        "• Your government-issued identity document\n\n"
        "The names must match exactly.",
        parse_mode="Markdown",
        reply_markup=cancel_menu,
    )

    return FULL_NAME


# ==========================================
# RECEIVE NAME
# ==========================================

async def receive_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.message.text == "❌ Cancel":

        context.user_data.pop("full_name", None)
        context.user_data.pop("id_document", None)
        context.user_data.pop("selfie_document", None)

        await update.message.reply_text(
            "❌ KYC submission cancelled.",
            reply_markup=(
                admin_menu
                if update.effective_user.id == ADMIN_ID
                else main_menu
            ),
        )

        return ConversationHandler.END

    context.user_data["full_name"] = update.message.text

    await update.message.reply_text(
        "*Step 2 of 3*\n\n"
        "📄 Upload ONE official identity document.\n\n"
        "Accepted documents:\n\n"
        "• National Identity Card\n"
        "• Passport\n"
        "• Driver's License\n\n"
        "You may upload either:\n"
        "• A photo\n"
        "• An image document\n"
        "• A PDF document",
        parse_mode="Markdown",
        reply_markup=cancel_menu,
    )

    return ID_DOCUMENT
  
# ==========================================
# RECEIVE ID DOCUMENT
# ==========================================

async def receive_id_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    # Cancel
    if update.message.text == "❌ Cancel":

        context.user_data.pop("full_name", None)
        context.user_data.pop("id_document", None)
        context.user_data.pop("selfie_document", None)

        await update.message.reply_text(
            "❌ KYC submission cancelled.",
            reply_markup=(
                admin_menu
                if update.effective_user.id == ADMIN_ID
                else main_menu
            ),
        )

        return ConversationHandler.END

    # Photo
    if update.message.photo:

        context.user_data["id_document"] = (
            update.message.photo[-1].file_id
        )

    # Document (PDF or Image)
    elif update.message.document:

        context.user_data["id_document"] = (
            update.message.document.file_id
        )

    else:

        await update.message.reply_text(
            "❌ Please upload a valid identity document."
        )

        return ID_DOCUMENT

    await update.message.reply_text(
        "*Step 3 of 3*\n\n"
        "🤳 Upload a clear selfie while holding the SAME identity document.\n\n"
        "Requirements:\n\n"
        "• Your face must be clearly visible.\n"
        "• The identity document must be readable.\n"
        "• Do not crop or edit the image.",
        parse_mode="Markdown",
        reply_markup=cancel_menu,
    )

    return SELFIE


# ==========================================
# RECEIVE SELFIE
# ==========================================

async def receive_selfie(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    # Cancel
    if update.message.text == "❌ Cancel":

        context.user_data.pop("full_name", None)
        context.user_data.pop("id_document", None)
        context.user_data.pop("selfie_document", None)
        await update.message.reply_text(
            "❌ KYC submission cancelled.",
            reply_markup=(
                admin_menu
                if update.effective_user.id == ADMIN_ID
                else main_menu
            ),
        )

        return ConversationHandler.END

    if not update.message.photo:

        await update.message.reply_text(
            "❌ Please upload a selfie photo."
        )

        return SELFIE

    context.user_data["selfie_document"] = (
        update.message.photo[-1].file_id
    )

    return await finish_kyc(update, context)


# ==========================================
# FINISH KYC
# ==========================================

async def finish_kyc(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    data = context.user_data

    # Save into database
    save_kyc(
        update.effective_user.id,
        data["full_name"],
        data["id_document"],
        data["selfie_document"],
    )

    # Notify Admin
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🪪 *NEW KYC SUBMISSION*\n\n"
            f"👤 Name: {data['full_name']}\n"
            f"🆔 User ID: {update.effective_user.id}"
        ),
        parse_mode="Markdown",
    )

    # Send Identity Document
    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=data["id_document"],
            caption="📄 Identity Document",
        )
    except Exception:
        await context.bot.send_document(
            chat_id=ADMIN_ID,
            document=data["id_document"],
            caption="📄 Identity Document",
        )

    # Send Selfie
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=data["selfie_document"],
        caption="🤳 Selfie Holding Identity Document",
    )

    # Confirm to user
    await update.message.reply_text(
        "✅ *KYC Submitted Successfully!*\n\n"
        "Your documents have been submitted to our Compliance Team.\n\n"
        "Your KYC status is now *Pending Review*.\n\n"
        "You will be notified once your verification has been completed.",
        parse_mode="Markdown",
        reply_markup=(
            admin_menu
            if update.effective_user.id == ADMIN_ID
            else main_menu
        ),
    )
    context.user_data.pop("full_name", None)
    context.user_data.pop("id_document", None)
    context.user_data.pop("selfie_document", None)
    return ConversationHandler.END
    
# ==========================================
# CANCEL KYC
# ==========================================

async def cancel_kyc(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    context.user_data.pop("full_name", None)
    context.user_data.pop("id_document", None)
    context.user_data.pop("selfie_document", None)
    await update.message.reply_text(
        "❌ KYC submission cancelled.",
        reply_markup=(
            admin_menu
            if update.effective_user.id == ADMIN_ID
            else main_menu
        ),
    )

    return ConversationHandler.END

# ==========================================
# KYC STATUS
# ==========================================

from database import get_kyc_status


async def kyc_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    status = get_kyc_status(update.effective_user.id)

    if status == "Not Submitted":

        message = (
            "🪪 *KYC Status*\n\n"
            "❌ Not Submitted\n\n"
            "Please submit your KYC verification."
        )

    elif status == "Pending":

        message = (
            "🪪 *KYC Status*\n\n"
            "🟡 Pending Review\n\n"
            "Our Compliance Team is reviewing your documents.\n\n"
            "Estimated review time:\n"
            "24–48 hours."
        )

    elif status == "Approved":

        message = (
            "🪪 *KYC Status*\n\n"
            "🟢 Approved\n\n"
            "Congratulations!\n\n"
            "Your identity has been successfully verified."
        )

    else:

        message = (
            "🪪 *KYC Status*\n\n"
            "🔴 Rejected\n\n"
            "Your verification was rejected.\n\n"
            "Please submit a new KYC application."
        )

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=(
            admin_menu
            if update.effective_user.id == ADMIN_ID
            else main_menu
        ),
    )
  
# ==========================================
# CONVERSATION HANDLER
# ==========================================

kyc_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex(r"^📤 Submit KYC$"),
            submit_kyc,
        ),
    ],

    states={
        FULL_NAME: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_name,
            ),
        ],

        ID_DOCUMENT: [
            MessageHandler(
                filters.PHOTO,
                receive_id_document,
            ),
            MessageHandler(
                filters.Document.ALL,
                receive_id_document,
            ),
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_id_document,
            ),
        ],

        SELFIE: [
            MessageHandler(
                filters.PHOTO,
                receive_selfie,
            ),
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_selfie,
            ),
        ],
    },

    fallbacks=[
        MessageHandler(
            filters.Regex(r"^❌ Cancel$"),
            cancel_kyc,
        ),
    ],

    allow_reentry=True,
)
