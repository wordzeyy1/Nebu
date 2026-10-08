from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)

from database import get_user

from keyboards import (
    main_menu,
    admin_menu,
)

from config import ADMIN_ID

BOT_USERNAME = "NebumineCloud_miningBot"


async def referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = get_user(update.effective_user.id)

    if not user:
        await update.message.reply_text(
            "❌ Please register first.",
            reply_markup=(
                admin_menu
                if update.effective_user.id == ADMIN_ID
                else main_menu
            ),
        )
        return

    referral_link = (
        f"https://t.me/{BOT_USERNAME}?start={update.effective_user.id}"
    )

    referrals_count = user[9]
    affiliate_balance = user[8]

    await update.message.reply_text(
        f"""
👥 <b>Referral Program</b>

🔗 <b>Your Referral Link</b>

<code>{referral_link}</code>

━━━━━━━━━━━━━━

👤 <b>Total Referrals</b>
{referrals_count}

💰 <b>Affiliate Earnings</b>
${affiliate_balance:,.2f}

Invite your friends using your personal referral link.

👥 Affiliate Program

━━━━━━━━━━━━━━━━━━

🎁 First Deposit Bonus

Earn 10% of your direct referral's first successful deposit.

Paid once per referral.

━━━━━━━━━━━━━━━━━━

💰 Mining Commission

Earn 5% of your direct referral's daily mining rewards for as long as they have active mining contracts.

━━━━━━━━━━━━━━━━━━

📌 Affiliate Withdrawal Policy

Affiliate commissions are credited to your Affiliate Balance.

To withdraw affiliate earnings, your account must own at least one active Cloud Mining contract.

━━━━━━━━━━━━━━━━━━

The more active miners you refer, the more recurring income you earn.
""",
        parse_mode=ParseMode.HTML,
        reply_markup=(
            admin_menu
            if update.effective_user.id == ADMIN_ID
            else main_menu
        ),
    )


referral_handler = MessageHandler(
    filters.Regex("^👥 Referrals$"),
    referrals,
)
