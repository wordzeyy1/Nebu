from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters


async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = """
📖 *Frequently Asked Questions*

━━━━━━━━━━━━━━━━━━

❓ *How do I start earning?*

• Register an account.
• Deposit funds.
• Purchase Cloud Mining Hash Power.
• Claim your mining rewards.

━━━━━━━━━━━━━━━━━━

💵 *Minimum Deposit*

• $50.00

━━━━━━━━━━━━━━━━━━

💸 *Minimum Withdrawal*

• $50.00

━━━━━━━━━━━━━━━━━━

⛏ *How does Cloud Mining work?*

Your purchased Hash Power generates mining rewards every day while your contract remains active.

━━━━━━━━━━━━━━━━━━

💰 *How do I claim rewards?*

Open *Crypto Cloud Mining* and tap *Claim Rewards*.

━━━━━━━━━━━━━━━━━━

👥 *How does the Affiliate Program work?*

You earn:

✅ 10% of your direct referral's first approved deposit.

✅ 5% of every mining reward claimed by your direct referrals.

━━━━━━━━━━━━━━━━━━

🪪 *Is KYC required?*

Yes.

KYC verification must be completed before withdrawals.

━━━━━━━━━━━━━━━━━━

⏳ *How long do deposits take?*

Deposits are credited after blockchain confirmation and admin approval.

━━━━━━━━━━━━━━━━━━

🏦 *How long do withdrawals take?*

Approved withdrawals are normally processed within a few hours.

━━━━━━━━━━━━━━━━━━

📦 *Can I own multiple mining contracts?*

Yes.

There is no limit to the number of active contracts you can own.

━━━━━━━━━━━━━━━━━━

❗ Need more help?

Use the *💬 Contact Support* button.
"""

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
    )


faq_handler = MessageHandler(
    filters.Regex("^📖 FAQs$"),
    faq,
  )
