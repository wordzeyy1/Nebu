from telegram import Update
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    CommandHandler,
    filters,
)

from database import add_deposit
from keyboards import (
    main_menu,
    admin_menu,
)

from config import ADMIN_ID

TXID = 0


async def submit_tx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📤 Please paste your Transaction Hash (TXID).\n\n"
        "After submitting, your transaction will be verified automatically."
    )
    return TXID


async def save_tx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txid = update.message.text.strip()

    network = context.user_data.get("network", "Unknown")
    usd_amount = context.user_data.get("usd_amount", 0)
    crypto_amount = context.user_data.get("crypto_amount", 0)

    add_deposit(
        update.effective_user.id,
        network,
        usd_amount,
        crypto_amount,
        txid
    )
    await context.bot.send_message(
    chat_id=ADMIN_ID,
    text=(
        "📥 *New Deposit Submitted*\n\n"
        f"👤 User ID: `{update.effective_user.id}`\n"
        f"🌐 Network: {network}\n"
        f"💵 Amount: ${usd_amount:,.2f}\n"
        f"🪙 Crypto: {crypto_amount:.8f}\n\n"
        f"🔗 TXID:\n`{txid}`\n\n"
        "Open *Admin Panel → Pending Deposits* to review."
    ),
    parse_mode="Markdown",
)

    await update.message.reply_text(
        f"""✅ *Deposit Submitted Successfully*

🌐 Network:
{network}

💵 Deposit Value:
${usd_amount:,.2f}

🪙 Amount Sent:
{crypto_amount:.8f}

📌 Status:
Pending Verification

━━━━━━━━━━━━━━

Your transaction has been received.

Our system will verify it on the blockchain automatically.

Once confirmed, your wallet balance will be credited.
""",
        parse_mode="Markdown",
        reply_markup=(
            admin_menu
            if update.effective_user.id == ADMIN_ID
            else main_menu
        ),
)

    # Clear temporary deposit data
    context.user_data.pop("network", None)
    context.user_data.pop("usd_amount", None)
    context.user_data.pop("crypto_amount", None)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "❌ Deposit submission cancelled.",
        reply_markup=(
            admin_menu
            if update.effective_user.id == ADMIN_ID
            else main_menu
        ),
    )

    return ConversationHandler.END


submit_tx_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex("^📤 Submit Transaction Hash$"),
            submit_tx,
        )
    ],
    states={
        TXID: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                save_tx,
            )
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel)
    ],
)
