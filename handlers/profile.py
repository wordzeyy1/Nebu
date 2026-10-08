from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from database import (
    get_user,
    get_total_hash_power,
    get_active_contracts,
    get_mining_balance,
    get_daily_earnings,
)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = get_user(update.effective_user.id)

    if not user:
        await update.message.reply_text(
            "❌ You are not registered.\n\n"
            "Please register first using 🆕 New User Registration."
        )
        return

    user_id = user[0]
    full_name = user[1]
    email = user[2]
    phone = user[3]
    country = user[4]
    withdrawal_address = user[5] if user[5] else "Not Set"
    kyc_status = user[6]
    wallet_balance = float(user[7])
    affiliate_balance = float(user[8])
    referrals = user[9]

    total_hash_power = get_total_hash_power(user_id)
    active_contracts = len(get_active_contracts(user_id))
    mining_balance = get_mining_balance(user_id)
    daily_earnings = get_daily_earnings(user_id)

    account_status = "Active"

    message = f"""👤 *MY PROFILE*

━━━━━━━━━━━━━━━━━━

🆔 *User ID*
`{user_id}`

👤 *Full Name*
{full_name}

📧 *Email*
{email}

📱 *Phone*
{phone}

🌍 *Country*
{country}

━━━━━━━━━━━━━━━━━━
💼 *WALLET*
━━━━━━━━━━━━━━━━━━

💵 Wallet Balance
`${wallet_balance:,.2f}`

💰 Affiliate Balance
`${affiliate_balance:,.2f}`

🏦 Default Withdrawal Address
`{withdrawal_address}`

━━━━━━━━━━━━━━━━━━
⛏ *CLOUD MINING*
━━━━━━━━━━━━━━━━━━

⚡ Total Hash Power
`{total_hash_power:.2f} TH/s`

📦 Active Contracts
`{active_contracts}`

💰 Mining Balance
`${mining_balance:,.2f}`

📈 Daily Earnings
`${daily_earnings:,.2f}`

━━━━━━━━━━━━━━━━━━
🛡 *ACCOUNT*
━━━━━━━━━━━━━━━━━━

🪪 KYC Status
{kyc_status}

👥 Referrals
{referrals}

🟢 Account Status
{account_status}
"""

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
    )


profile_handler = MessageHandler(
    filters.Regex("^📋 My Profile$"),
    profile,
    )
