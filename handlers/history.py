from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)

from database import (
    get_wallet_transactions,
    get_user_withdrawals,
)


async def transaction_history(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    transactions = get_wallet_transactions(
        update.effective_user.id
    )

    if not transactions:

        await update.message.reply_text(
            "📜 Transaction History\n\n"
            "No wallet transactions found."
        )

        return

    message = "📜 *Transaction History*\n\n"

    for tx in transactions:

        transaction_type = tx[0]
        amount = float(tx[1])
        reason = tx[2]
        date = tx[3]

        sign = "➕"

        if transaction_type in (
            "Debit",
            "Withdrawal",
        ):
            sign = "➖"

        message += (
            f"{sign} *{transaction_type}*\n"
            f"${amount:,.2f}\n"
            f"{reason}\n"
            f"📅 {date}\n\n"
        )

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
    )

async def withdrawal_history(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    withdrawals = get_user_withdrawals(
        update.effective_user.id
    )

    if not withdrawals:

        await update.message.reply_text(
            "📋 Withdrawal History\n\n"
            "You have not made any withdrawal requests."
        )

        return

    message = "📋 *Withdrawal History*\n\n"

    for withdrawal in withdrawals:

        amount = float(withdrawal[0])
        cryptocurrency = withdrawal[1]
        wallet = withdrawal[2]
        status = withdrawal[3]
        reason = withdrawal[4]
        txid = withdrawal[5]
        date = withdrawal[6]

        if status == "Approved":
            icon = "✅"
        elif status == "Rejected":
            icon = "❌"
        else:
            icon = "🟡"

        message += (
            f"{icon} *{status}*\n"
            f"💵 ${amount:,.2f}\n"
            f"🪙 {cryptocurrency}\n"
            f"📅 {date}\n"
        )

        if status == "Approved" and txid:
            message += (
                f"🔗 TXID:\n"
                f"`{txid}`\n"
            )

        if status == "Rejected" and reason:
            message += (
                f"❌ Reason:\n"
                f"{reason}\n"
            )

        message += "\n"

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        )
    
history_handler = MessageHandler(
    filters.Regex("^📜 Transaction History$"),
    transaction_history,
        )

withdrawal_history_handler = MessageHandler(
    filters.Regex("^📋 Withdrawal History$"),
    withdrawal_history,
        )
