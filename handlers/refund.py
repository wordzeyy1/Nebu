# ==========================================
# IMPORTS
# ==========================================

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
from database import add_refund
from keyboards import (
    main_menu,
    admin_menu,
)

# ==========================================
# CONVERSATION STATES
# ==========================================

(
    DATE,
    PROFILE,
    AMOUNT,
    CRYPTO,
    WALLET,
    ADDRESS,
    EVIDENCE,
) = range(7)


# ==========================================
# KEYBOARDS
# ==========================================

cancel_menu = ReplyKeyboardMarkup(
    [["❌ Cancel"]],
    resize_keyboard=True,
    one_time_keyboard=False,
)

done_keyboard = ReplyKeyboardMarkup(
    [["✅ Done", "❌ Cancel"]],
    resize_keyboard=True,
    one_time_keyboard=False,
)


# ==========================================
# CANCEL REFUND
# ==========================================

async def cancel_refund(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.clear()

    await update.message.reply_text(
        "❌ Refund request cancelled.",
        reply_markup=(
            admin_menu
            if update.effective_user.id == ADMIN_ID
            else main_menu
        ),
    )

    return ConversationHandler.END

# ==========================================
# STEP 1 OF 7
# ==========================================

async def refund_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.clear()
    context.user_data["refund_photos"] = []
    context.user_data["refund_text"] = ""

    await update.message.reply_text(
        "💰 *Refund Request Form*\n\n"
        "*Step 1 of 7*\n\n"
        "📅 When did you make the investment?\n\n"
        "Example:\n"
        "15 June 2025",
        parse_mode="Markdown",
        reply_markup=cancel_menu,
    )

    return DATE

async def investment_date(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text == "❌ Cancel":
        return await cancel_refund(update, context)

    context.user_data["investment_date"] = update.message.text

    await update.message.reply_text(
        "*Step 2 of 7*\n\n"

        "👤 What is your account Username or User ID associated with your profile?\n\n"

        "Example:\n"

        "Username: JohnDoe\n\n"

        "or\n\n"

        "User ID: 123456789",
        parse_mode="Markdown",
        reply_markup=cancel_menu,
    )

    return PROFILE

async def profile_id(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text == "❌ Cancel":
        return await cancel_refund(update, context)

    context.user_data["profile_id"] = update.message.text

    await update.message.reply_text(
        "*Step 3 of 7*\n\n"

        "💵 What amount did you invest?\n\n"

        "Example:\n"

        "$250",
        parse_mode="Markdown",
        reply_markup=cancel_menu,
    )

    return AMOUNT

async def investment_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text == "❌ Cancel":
        return await cancel_refund(update, context)

    context.user_data["investment_amount"] = update.message.text

    await update.message.reply_text(
        "*Step 4 of 7*\n\n"

        "🪙 Which cryptocurrency/network was used for the deposit?\n\n"

        "Examples:\n\n"

        "• BTC\n"
        "• ETH\n"
        "• USDT (TRC20)\n"
        "• USDT (ERC20)\n"
        "• USDC (ERC20)",
        parse_mode="Markdown",
        reply_markup=cancel_menu,
    )

    return CRYPTO

async def cryptocurrency(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text == "❌ Cancel":
        return await cancel_refund(update, context)

    context.user_data["cryptocurrency"] = update.message.text

    await update.message.reply_text(
        "*Step 5 of 7*\n\n"

        "🏦 Which exchange or wallet did you use to send the funds?\n\n"

        "Examples:\n\n"

        "• Binance\n"
        "• Trust Wallet\n"
        "• Coinbase\n"
        "• Bybit\n"
        "• OKX\n"
        "• MetaMask\n"
        "• Klever Wallet",
        parse_mode="Markdown",
        reply_markup=cancel_menu,
    )

    return WALLET

async def exchange_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text == "❌ Cancel":
        return await cancel_refund(update, context)

    context.user_data["exchange_wallet"] = update.message.text

    await update.message.reply_text(
        "*Step 6 of 7*\n\n"

        "📤 What wallet address did you send the funds from?\n\n"

        "Please paste the complete sending wallet address.",
        parse_mode="Markdown",
        reply_markup=cancel_menu,
    )

    return ADDRESS

async def sender_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text == "❌ Cancel":
        return await cancel_refund(update, context)

    context.user_data["sender_wallet"] = update.message.text
    context.user_data["refund_text"] = ""
    context.user_data["refund_photos"] = []

    await update.message.reply_text(
        "*Step 7 of 7*\n\n"

        "📎 Provide your transaction evidence.\n\n"

        "Please upload:\n\n"

        "• Transaction Hash (TXID)\n"
        "• Deposit Receipt\n"
        "• Screenshot(s)\n"
        "• Photo(s)\n\n"

        "If you have multiple transactions, label them clearly.\n\n"

        "Example:\n\n"

        "Transaction 1\n\n"

        "TXID:\n"

        "xxxxxxxxxxxxxxxxxxxxxxxx\n\n"

        "Transaction 2\n\n"

        "TXID:\n"

        "yyyyyyyyyyyyyyyyyyyyyyyy\n\n"

        "📷 You may upload multiple screenshots or photos.\n\n"

        "When you have finished uploading everything, press ✅ Done.",
        parse_mode="Markdown",
        reply_markup=done_keyboard,
    )

    return EVIDENCE

# ==========================================
# RECEIVE PHOTO
# ==========================================

async def receive_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    photo = update.message.photo[-1]

    context.user_data["refund_photos"].append(photo.file_id)

    await update.message.reply_text(
        "✅ Photo saved.\n\n"
        "Send another photo, TXID or press ✅ Done.",
        reply_markup=done_keyboard,
    )

    return EVIDENCE


# ==========================================
# RECEIVE IMAGE DOCUMENT
# ==========================================

async def receive_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    document = update.message.document

    if (
        document
        and document.mime_type
        and document.mime_type.startswith("image/")
    ):
        context.user_data["refund_photos"].append(document.file_id)

        await update.message.reply_text(
            "✅ Image saved.\n\n"
            "Upload another image or press ✅ Done.",
            reply_markup=done_keyboard,
        )

    return EVIDENCE


# ==========================================
# RECEIVE TEXT EVIDENCE
# ==========================================

async def receive_evidence_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    text = update.message.text

    # Cancel
    if text == "❌ Cancel":
        return await cancel_refund(update, context)

    # Finish
    if text == "✅ Done":
        return await finish_refund(update, context)

    current = context.user_data.get("refund_text", "")

    if current:
        current += "\n\n"

    context.user_data["refund_text"] = current + text

    await update.message.reply_text(
        "✅ Evidence saved.\n\n"
        "Send more screenshots, photos or TXIDs.\n"
        "Press ✅ Done when finished.",
        reply_markup=done_keyboard,
    )

    return EVIDENCE


# ==========================================
# FINISH REFUND
# ==========================================

async def finish_refund(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    data = context.user_data

    # Save refund to database
    add_refund(
        user_id=update.effective_user.id,
        full_name=update.effective_user.full_name,
        investment_date=data.get("investment_date", ""),
        profile_id=data.get("profile_id", ""),
        investment_amount=data.get("investment_amount", ""),
        cryptocurrency=data.get("cryptocurrency", ""),
        exchange_wallet=data.get("exchange_wallet", ""),
        sender_wallet=data.get("sender_wallet", ""),
        evidence_text=data.get("refund_text", ""),
        evidence_file_ids="|".join(
            data.get("refund_photos", [])
        ),
    )

    # Notify admin
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "💰 *NEW REFUND REQUEST*\n\n"
            f"👤 Name: {update.effective_user.full_name}\n"
            f"🆔 User ID: {update.effective_user.id}\n\n"
            f"📅 Investment Date: {data.get('investment_date', '')}\n"
            f"🪪 Profile ID: {data.get('profile_id', '')}\n"
            f"💵 Amount: {data.get('investment_amount', '')}\n"
            f"🪙 Cryptocurrency: {data.get('cryptocurrency', '')}\n"
            f"🏦 Exchange Wallet: {data.get('exchange_wallet', '')}\n"
            f"📤 Sender Wallet: {data.get('sender_wallet', '')}\n\n"
            f"📝 Evidence:\n{data.get('refund_text', '')}"
        ),
        parse_mode="Markdown",
    )

    # Send uploaded photos to admin
    for photo in data.get("refund_photos", []):
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo,
        )

    # Confirm to user
    await update.message.reply_text(
        "✅ *Your refund request has been submitted successfully.*\n\n"
        "Your request has been forwarded to our *Refund Review Team*.\n\n"
        "To help speed up the investigation and any eligible refund or balance credit, "
        "please complete your *Know Your Customer (KYC)* verification if you have not already done so.\n\n"
        "Completing KYC helps us verify account ownership, protect your funds, and process approved refund requests more efficiently.\n\n"
        "You will be notified once the review has been completed.",
        parse_mode="Markdown",
        reply_markup=(
            admin_menu
            if update.effective_user.id == ADMIN_ID
            else main_menu
        ),
    )

    context.user_data.clear()

    return ConversationHandler.END

refund_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex("^💰 Submit Refund Request$"),
            refund_request,
        ),
    ],

    states={
        DATE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, investment_date),
        ],

        PROFILE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, profile_id),
        ],

        AMOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, investment_amount),
        ],

        CRYPTO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, cryptocurrency),
        ],

        WALLET: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, exchange_wallet),
        ],

        ADDRESS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, sender_wallet),
        ],

        EVIDENCE: [
            MessageHandler(filters.PHOTO, receive_photo),
            MessageHandler(filters.Document.IMAGE, receive_document),
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_evidence_text),
        ],
    },

    fallbacks=[
        MessageHandler(
            filters.Regex("^❌ Cancel$"),
            cancel_refund,
        ),
    ],
)
