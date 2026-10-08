from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import ADMIN_ID
from database import admin_wallet_adjustment
from keyboards import admin_menu

USER_ID, AMOUNT, REASON = range(3)

cancel_keyboard = ReplyKeyboardMarkup(
    [["❌ Cancel"]],
    resize_keyboard=True,
)


# ==========================================
# START CREDIT
# ==========================================

async def start_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data["transaction_type"] = "Credit"

    await update.message.reply_text(
        "➕ Wallet Credit\n\n"
        "Enter the User ID:",
        reply_markup=cancel_keyboard,
    )

    return USER_ID


# ==========================================
# START DEBIT
# ==========================================

async def start_debit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data["transaction_type"] = "Debit"

    await update.message.reply_text(
        "➖ Wallet Debit\n\n"
        "Enter the User ID:",
        reply_markup=cancel_keyboard,
    )

    return USER_ID


# ==========================================
# RECEIVE USER ID
# ==========================================

async def receive_user(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text == "❌ Cancel":

        await update.message.reply_text(
            "Cancelled.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    try:
        context.user_data["user_id"] = int(update.message.text)

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid User ID."
        )

        return USER_ID

    await update.message.reply_text(
        "Enter the amount.\n\n"
        "Example:\n"
        "100",
        reply_markup=cancel_keyboard,
    )

    return AMOUNT


# ==========================================
# RECEIVE AMOUNT
# ==========================================

async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text == "❌ Cancel":

        await update.message.reply_text(
            "Cancelled.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    try:
        amount = float(update.message.text)

        if amount <= 0:
            raise ValueError

    except ValueError:

        await update.message.reply_text(
            "❌ Please enter a valid amount."
        )

        return AMOUNT

    context.user_data["amount"] = amount

    await update.message.reply_text(
        "📝 Enter the reason for this transaction.\n\n"
        "Examples:\n"
        "• Referral Bonus\n"
        "• Manual Wallet Adjustment\n"
        "• Refund Credit\n"
        "• Duplicate Deposit Reversal",
        reply_markup=cancel_keyboard,
    )

    return REASON


# ==========================================
# RECEIVE REASON
# ==========================================

async def receive_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text == "❌ Cancel":

        await update.message.reply_text(
            "Cancelled.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    reason = update.message.text

    success = admin_wallet_adjustment(
        user_id=context.user_data["user_id"],
        amount=context.user_data["amount"],
        transaction_type=context.user_data["transaction_type"],
        reason=reason,
    )

    if not success:

        await update.message.reply_text(
            "❌ Transaction failed.\n\n"
            "Possible reasons:\n"
            "• User not found\n"
            "• Insufficient wallet balance",
            reply_markup=admin_menu,
        )

        context.user_data.clear()

        return ConversationHandler.END

    sign = (
        "+"
        if context.user_data["transaction_type"] == "Credit"
        else "-"
    )

    # Notify user
    await context.bot.send_message(
        chat_id=context.user_data["user_id"],
        text=(
            "💳 Wallet Update\n\n"
            f"Type: {context.user_data['transaction_type']}\n"
            f"Amount: {sign}${context.user_data['amount']:,.2f}\n\n"
            f"Reason:\n{reason}"
        ),
    )

    # Notify admin
    await update.message.reply_text(
        "✅ Wallet updated successfully.",
        reply_markup=admin_menu,
    )

    context.user_data.clear()

    return ConversationHandler.END


# ==========================================
# CANCEL
# ==========================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "Cancelled.",
        reply_markup=admin_menu,
    )

    return ConversationHandler.END


# ==========================================
# HANDLER
# ==========================================

admin_wallet_handler = ConversationHandler(

    entry_points=[

        MessageHandler(
            filters.Regex(r"^💳 Credit Wallet$"),
            start_credit,
        ),

        MessageHandler(
            filters.Regex("^➖ Debit Wallet$"),
            start_debit,
        ),

    ],

    states={

        USER_ID: [

            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_user,
            ),

        ],

        AMOUNT: [

            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_amount,
            ),

        ],

        REASON: [

            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_reason,
            ),

        ],

    },

    fallbacks=[

        MessageHandler(
            filters.Regex("^❌ Cancel$"),
            cancel,
        ),

    ],

                      )
