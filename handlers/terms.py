from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters


async def terms(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = """
📜 *Terms & Conditions*

━━━━━━━━━━━━━━━━━━

1️⃣ Users must provide accurate registration information.

2️⃣ KYC verification is required before withdrawals.

    Withdrawal address linking is required on first withdrawal application through the pro Bot (Tax differs 3%-5%) Refunded upon completion of the withdrawal amount,"Example withdrawal amount+ (3%)=Withdrawal address

3️⃣ Deposits become available after admin approval.

4️⃣ Mining rewards are generated only by active Cloud Mining contracts.

5️⃣ Users may own multiple mining contracts.

6️⃣ Referral commissions are earned only through legitimate referrals.

7️⃣ First Deposit Bonus:
10% of a direct referral's first approved deposit.

8️⃣ Mining Referral Bonus:
5% of every mining reward claimed by your direct referrals.

9️⃣ Affiliate earnings are credited to the Affiliate Balance.

🔟 Affiliate Balance must first be used to purchase Cloud Mining Hash Power before it becomes eligible for withdrawal.

1️⃣1️⃣ Fraudulent activities, fake deposits or abuse of the referral system may result in account suspension.

1️⃣2️⃣ Nebumine pro reserves the right to modify platform policies whenever necessary.
"""

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
    )


terms_handler = MessageHandler(
    filters.Regex("^📜 Terms & Conditions$"),
    terms,
  )
