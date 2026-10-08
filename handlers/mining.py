from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from telegram import ReplyKeyboardMarkup

from datetime import datetime

from config import HASH_PRICE, DAILY_ROI

from database import (
    user_exists,
    get_total_hash_power,
    get_daily_earnings,
    get_weekly_earnings,
    get_monthly_earnings,
    get_mining_balance,
    get_active_contracts,
    create_mining_contract,
    calculate_claim,
    update_last_claim,
    save_claim,
    get_user,
    update_wallet_balance,
    update_affiliate_balance,
    record_wallet_transaction,
    pay_mining_referral_bonus,
)

from handlers.event_broadcast import (
    broadcast_contract_purchase,
    broadcast_mining_reward,
)

from keyboards import main_menu

from handlers.main_menu_override import main_menu_override

BUY_HASH = 0
PAYMENT_METHOD = 1

cancel_keyboard = ReplyKeyboardMarkup(
    [
        ["❌ Cancel"],
    ],
    resize_keyboard=True,
)


async def mining_dashboard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    if not user_exists(user_id):
        await update.message.reply_text(
            "🪙⛏ *Crypto Cloud Mining*\n\n"
            "You need to register before you can access Crypto Cloud Mining.\n\n"
            "Please tap *🆕 New User Registration* from the main menu to create your account.",
            parse_mode="Markdown",
        )
        return

    user = get_user(user_id)

    wallet_balance = user[7]

    hash_power = get_total_hash_power(user_id)

    mining_balance = get_mining_balance(user_id)

    daily = get_daily_earnings(user_id)

    weekly = get_weekly_earnings(user_id)

    monthly = get_monthly_earnings(user_id)

    contracts = len(get_active_contracts(user_id))

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🛒 Buy Hash Power",
                callback_data="buy_hashpower",
            )
        ],
        [
            InlineKeyboardButton(
                "💰 Claim Rewards",
                callback_data="claim_rewards",
            )
        ],
        [
            InlineKeyboardButton(
                "📜 Active Contracts",
                callback_data="contracts",
            )
        ],
    ])

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    await update.message.reply_text(
        f"""
⛏ *Nebumine pro Cloud Mining*

━━━━━━━━━━━━━━━━━━

💵 *Wallet Balance*

`${wallet_balance:,.2f}`

━━━━━━━━━━━━━━━━━━

⚡ *Total Hash Power*

`{hash_power:.2f} TH/s`

━━━━━━━━━━━━━━━━━━

💰 *Mining Balance*

`${mining_balance:,.2f}`

━━━━━━━━━━━━━━━━━━

📈 *Daily Earnings*

`${daily:,.2f}`

📆 *Weekly Earnings*

`${weekly:,.2f}`

🗓 *Monthly Earnings*

`${monthly:,.2f}`

━━━━━━━━━━━━━━━━━━

📦 *Active Contracts*

`{contracts}`

━━━━━━━━━━━━━━━━━━

🕒 *Last Updated*

`{now}`
""",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def buy_hashpower(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "⚡ Enter the amount of TH/s you wish to purchase.\n\n"
        f"Current Price:\n"
        f"${HASH_PRICE:.2f} per TH/s",
        reply_markup=cancel_keyboard,
    )
    return BUY_HASH


async def process_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Cancel purchase
    if update.message.text == "❌ Cancel":

        context.user_data.pop("hash_power", None)
        context.user_data.pop("cost", None)

        return await main_menu_override(update, context)

    try:
        hash_power = float(update.message.text)

    except ValueError:

        await update.message.reply_text(
            "❌ Please enter a valid Hash Power amount."
        )

        return BUY_HASH

    if hash_power <= 0:

        await update.message.reply_text(
            "❌ Hash Power must be greater than zero."
        )

        return BUY_HASH

    cost = hash_power * HASH_PRICE

    # Save purchase details
    context.user_data["hash_power"] = hash_power
    context.user_data["cost"] = cost

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💵 Wallet Balance",
                    callback_data="wallet_payment",
                )
            ],
            [
                InlineKeyboardButton(
                    "👥 Affiliate Balance",
                    callback_data="affiliate_payment",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="cancel_purchase",
                )
            ],
        ]
    )

    await update.message.reply_text(
        f"""
🛒 *Purchase Summary*

━━━━━━━━━━━━━━━━━━

⚡ Hash Power

`{hash_power:.2f} TH/s`

💰 Total Cost

`${cost:,.2f}`

━━━━━━━━━━━━━━━━━━

Choose how you would like to pay for this mining contract.
""",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

    return PAYMENT_METHOD

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "cancel_purchase":

        context.user_data.pop("hash_power", None)
        context.user_data.pop("cost", None)

        await query.edit_message_reply_markup(reply_markup=None)

        await query.message.reply_text(
            "❌ Purchase cancelled.",
            reply_markup=main_menu,
        )

        return ConversationHandler.END

    user = get_user(query.from_user.id)

    wallet_balance = float(user[7])
    affiliate_balance = float(user[8])

    hash_power = context.user_data["hash_power"]
    cost = context.user_data["cost"]

    # ----------------------------
    # Wallet Balance Payment
    # ----------------------------
    if query.data == "wallet_payment":

        if wallet_balance < cost:

            context.user_data.pop("hash_power", None)
            context.user_data.pop("cost", None)

            await query.edit_message_reply_markup(reply_markup=None)

            await query.message.reply_text(
                "❌ Insufficient Wallet Balance.",
                reply_markup=main_menu,
            )

            return ConversationHandler.END

        update_wallet_balance(
            query.from_user.id,
            -cost,
        )

        payment_source = "Wallet Balance"

    # ----------------------------
    # Affiliate Balance Payment
    # ----------------------------
    elif query.data == "affiliate_payment":

        if affiliate_balance < cost:

            context.user_data.pop("hash_power", None)
            context.user_data.pop("cost", None)

            await query.edit_message_reply_markup(reply_markup=None)

            await query.message.reply_text(
                "❌ Insufficient Affiliate Balance.",
                reply_markup=main_menu,
            )

            return ConversationHandler.END

        update_affiliate_balance(
            query.from_user.id,
            -cost,
        )

        payment_source = "Affiliate Balance"

    # ----------------------------
    # Activate Contract
    # ----------------------------
    daily_income = cost * (DAILY_ROI / 100)

    create_mining_contract(
        query.from_user.id,
        hash_power,
        cost,
        daily_income,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    record_wallet_transaction(
        user_id=query.from_user.id,
        transaction_type="Mining Contract",
        amount=cost,
        reason=f"Purchased using {payment_source}",
    )
    
    await broadcast_contract_purchase(
        bot=context.bot,
        user_id=update.effective_user.id,
        hash_power=hash_power,
        investment=cost,
        daily_earnings=daily_income,
    )

    await query.edit_message_reply_markup(reply_markup=None)

    await query.message.reply_text(
        f"""
✅ *Mining Contract Activated!*

━━━━━━━━━━━━━━━━━━

⚡ Hash Power

`{hash_power:.2f} TH/s`

💰 Cost

`${cost:,.2f}`

💳 Paid Using

{payment_source}

📈 Daily Earnings

`${daily_income:.2f}`
""",
        parse_mode="Markdown",
        reply_markup=main_menu,
    )

    context.user_data.pop("hash_power", None)
    context.user_data.pop("cost", None)

    return ConversationHandler.END


async def claim_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    total, claims = calculate_claim(user_id)

    if total <= 0:

        await query.message.reply_text(
            "⛏ No mining rewards available yet.\n\n"
            "Keep mining and try again later."
        )

        return

    # Credit mining reward
    update_wallet_balance(
        user_id,
        total,
    )

    record_wallet_transaction(
        user_id=user_id,
        transaction_type="Mining Reward",
        amount=total,
        reason="Daily Mining Reward",
    )
    
    await broadcast_mining_reward(
        bot=context.bot,
        user_id=user_id,
        reward_amount=total,
    )

    # =====================================
    # PAY AFFILIATE COMMISSION
    # =====================================

    result = pay_mining_referral_bonus(
        user_id,
        total,
    )

    if result:

        referrer_id, commission = result

        await context.bot.send_message(
            chat_id=referrer_id,
            text=(
                "🎉 *Affiliate Commission Earned!*\n\n"
                "One of your direct referrals has claimed mining rewards.\n\n"
                f"💰 Commission Earned: *${commission:,.2f}*\n\n"
                "The commission has been added to your Affiliate Balance."
            ),
            parse_mode="Markdown",
        )

    # =====================================

    for contract_id, amount in claims:

        save_claim(
            user_id,
            contract_id,
            amount,
        )

        update_last_claim(
            contract_id,
        )

    await query.message.reply_text(
        f"✅ Rewards Claimed Successfully!\n\n"
        f"💰 ${total:,.2f} has been added to your wallet."
    )


async def active_contracts(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    contracts = get_active_contracts(query.from_user.id)

    if not contracts:

        await query.message.reply_text(
            "📭 You don't have any active mining contracts."
        )

        return

    text = "📜 *Active Mining Contracts*\n\n"

    for i, contract in enumerate(contracts, start=1):

        text += (
            f"━━━━━━━━━━━━━━\n"
            f"⚡ *Contract #{i}*\n\n"
            f"Hash Power: *{contract[2]:.2f} TH/s*\n"
            f"Purchase Price: *${contract[3]:,.2f}*\n"
            f"Daily Income: *${contract[4]:,.2f}*\n"
            f"Purchase Date:\n"
            f"{contract[5]}\n\n"
            f"Status: 🟢 {contract[7]}\n\n"
        )

    await query.message.reply_text(
        text,
        parse_mode="Markdown",
    )


mining_handler = MessageHandler(
    filters.Regex("^🪙⛏ Crypto Cloud Mining$"),
    mining_dashboard,
)

buy_hashpower_handler = ConversationHandler(

    entry_points=[
        CallbackQueryHandler(
            buy_hashpower,
            pattern="^buy_hashpower$",
        )
    ],

    states={

        BUY_HASH: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                process_purchase,
            )
        ],

        PAYMENT_METHOD: [
            CallbackQueryHandler(
                process_payment,
                pattern="^(wallet_payment|affiliate_payment|cancel_purchase)$",
            )
        ],

    },

    fallbacks=[
        MessageHandler(
            filters.Regex("^🏠 Main Menu$"),
            main_menu_override,
        )
    ],

)

claim_rewards_handler = CallbackQueryHandler(
    claim_rewards,
    pattern="^claim_rewards$",
)

contracts_handler = CallbackQueryHandler(
    active_contracts,
    pattern="^contracts$",
)
