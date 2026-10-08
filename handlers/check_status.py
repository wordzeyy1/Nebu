from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)

from database import (
    get_kyc_status,
    get_latest_deposit_status,
    get_latest_refund_status,
)

from keyboards import (
    main_menu,
    admin_menu,
)

from config import ADMIN_ID


async def check_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    kyc = get_kyc_status(user_id)

    deposit = get_latest_deposit_status(user_id)

    refund = get_latest_refund_status(user_id)

    message = f"""
📊 <b>Account Status</b>

━━━━━━━━━━━━━━

🪪 <b>KYC</b>
{kyc}

💳 <b>Latest Deposit</b>
{deposit}

💰 <b>Refund Request</b>
{refund}

━━━━━━━━━━━━━━

Thank you for using Nebumine pro.
"""

    await update.message.reply_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=(
            admin_menu
            if update.effective_user.id == ADMIN_ID
            else main_menu
        ),
    )


check_status_handler = MessageHandler(
    filters.Regex("^📊 Check Status$"),
    check_status,
)
