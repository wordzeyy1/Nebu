from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from datetime import datetime

from config import ADMIN_ID, DAILY_ROI

from database import (
    user_exists,
    get_user,
    create_mining_contract,
)

from keyboards import admin_menu


USER_ID, HASH_POWER, PURCHASE_PRICE = range(3)


cancel_keyboard = ReplyKeyboardMarkup(
    [
        ["❌ Cancel"],
    ],
    resize_keyboard=True,
)


# ==========================================
# START GRANT CONTRACT
# ==========================================

async def start_grant_contract(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    context.user_data.clear()

    await update.message.reply_text(
        "⛏ *Grant Mining Contract*\n\n"
        "Enter the Telegram User ID:",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard,
    )

    return USER_ID


# ==========================================
# RECEIVE USER ID
# ==========================================

async def receive_contract_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.message.text == "❌ Cancel":

        await update.message.reply_text(
            "❌ Cancelled.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    try:
        user_id = int(update.message.text.strip())

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid User ID.\n\n"
            "Please enter the numeric Telegram User ID."
        )

        return USER_ID

    if not user_exists(user_id):

        await update.message.reply_text(
            "❌ User not found.\n\n"
            "Please check the User ID and try again."
        )

        return USER_ID

    context.user_data["contract_user_id"] = user_id

    await update.message.reply_text(
        "⚡ Enter the Hash Power.\n\n"
        "Example:\n"
        "100"
    )

    return HASH_POWER


# ==========================================
# RECEIVE HASH POWER
# ==========================================

async def receive_hash_power(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.message.text == "❌ Cancel":

        await update.message.reply_text(
            "❌ Cancelled.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    try:
        hash_power = float(update.message.text.strip())

        if hash_power <= 0:
            raise ValueError

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid Hash Power.\n\n"
            "Enter a number greater than zero."
        )

        return HASH_POWER

    context.user_data["contract_hash_power"] = hash_power

    await update.message.reply_text(
        "💰 Enter the Contract Value.\n\n"
        "This is the contract value used to calculate its daily mining income.\n\n"
        "Example:\n"
        "100"
    )

    return PURCHASE_PRICE


# ==========================================
# RECEIVE CONTRACT VALUE
# ==========================================

async def receive_purchase_price(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.message.text == "❌ Cancel":

        await update.message.reply_text(
            "❌ Cancelled.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    try:
        purchase_price = float(update.message.text.strip())

        if purchase_price <= 0:
            raise ValueError

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid contract value.\n\n"
            "Enter a number greater than zero."
        )

        return PURCHASE_PRICE

    user_id = context.user_data["contract_user_id"]
    hash_power = context.user_data["contract_hash_power"]

    daily_income = purchase_price * (DAILY_ROI / 100)

    purchase_date = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # ==========================================
    # CREATE ACTIVE CONTRACT
    # ==========================================

    result = create_mining_contract(
        user_id=user_id,
        hash_power=hash_power,
        purchase_price=purchase_price,
        daily_income=daily_income,
        purchase_date=purchase_date,
    )

    if not result:

        await update.message.reply_text(
            "❌ Failed to create the mining contract.",
            reply_markup=admin_menu,
        )

        context.user_data.clear()

        return ConversationHandler.END

    # ==========================================
    # GET USER NAME
    # ==========================================

    user = get_user(user_id)

    if user:
        full_name = user[1]
    else:
        full_name = "User"

    # ==========================================
    # NOTIFY USER
    # ==========================================

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "🎉 *Mining Contract Granted!*\n\n"
            "An administrator has activated a mining contract "
            "on your NebuMine Pro account.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"⚡ Hash Power: *{hash_power:.2f} TH/s*\n"
            f"💰 Contract Value: *${purchase_price:,.2f}*\n"
            f"📈 Daily Earnings: *${daily_income:,.2f}*\n"
            f"🟢 Status: *Active*\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Your contract is now active and mining rewards "
            "will accumulate automatically."
        ),
        parse_mode="Markdown",
    )

    # ==========================================
    # CONFIRM TO ADMIN
    # ==========================================

    await update.message.reply_text(
        "✅ *Mining Contract Granted Successfully!*\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 User: {full_name}\n"
        f"🆔 User ID: `{user_id}`\n"
        f"⚡ Hash Power: `{hash_power:.2f} TH/s`\n"
        f"💰 Contract Value: `${purchase_price:,.2f}`\n"
        f"📈 Daily Earnings: `${daily_income:,.2f}`\n"
        "🟢 Status: `Active`\n\n"
        "The user's wallet was not debited.",
        parse_mode="Markdown",
        reply_markup=admin_menu,
    )

    context.user_data.clear()

    return ConversationHandler.END


# ==========================================
# CANCEL
# ==========================================

async def cancel_grant_contract(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    context.user_data.clear()

    await update.message.reply_text(
        "❌ Contract creation cancelled.",
        reply_markup=admin_menu,
    )

    return ConversationHandler.END


# ==========================================
# HANDLER
# ==========================================

admin_contract_handler = ConversationHandler(

    entry_points=[
        MessageHandler(
            filters.Regex("^⛏ Grant Mining Contract$"),
            start_grant_contract,
        )
    ],

    states={

        USER_ID: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_contract_user,
            )
        ],

        HASH_POWER: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_hash_power,
            )
        ],

        PURCHASE_PRICE: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_purchase_price,
            )
        ],
    },

    fallbacks=[
        MessageHandler(
            filters.Regex("^❌ Cancel$"),
            cancel_grant_contract,
        )
    ],
)
