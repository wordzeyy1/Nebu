from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import requests

from keyboards import (
    wallet_menu,
    cancel_menu,
)

from config import ADMIN_ID

from database import (
    get_kyc_status,
    get_wallet_balance,
    create_withdrawal,
    admin_wallet_adjustment,
    record_wallet_transaction,
)


CRYPTO, AMOUNT, ADDRESS = range(3)


# ==========================================
# CRYPTO WITHDRAWAL KEYBOARD
# ==========================================

withdraw_crypto_keyboard = ReplyKeyboardMarkup(
    [
        ["₿ Withdraw BTC", "♦ Withdraw ETH"],
        ["💲 Withdraw USDT (TRC20)"],
        ["💲 Withdraw USDT (ERC20)"],
        ["💲 Withdraw USDC (ERC20)"],
        ["❌ Cancel"],
    ],
    resize_keyboard=True,
)


# ==========================================
# LIVE CRYPTO PRICE
# ==========================================

def get_live_crypto_price(crypto):
    """
    Get the current BTC/USD or ETH/USD spot price.

    Returns:
        float | None
    """

    pair_map = {
        "BTC": "BTC-USD",
        "ETH": "ETH-USD",
    }

    pair = pair_map.get(crypto)

    if not pair:
        return None

    try:

        response = requests.get(
            f"https://api.coinbase.com/v2/prices/{pair}/spot",
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        price = float(
            data["data"]["amount"]
        )

        if price <= 0:
            return None

        return price

    except Exception as e:

        print(
            f"Failed to get live {crypto} price: {e}"
        )

        return None


# ==========================================
# USD → CRYPTO CONVERSION
# ==========================================

def convert_usd_to_crypto(amount, crypto):
    """
    Convert USD withdrawal amount to crypto.

    BTC/ETH:
        Uses live market price.

    USDT/USDC:
        Uses approximately 1:1 USD conversion.

    Returns:
        (crypto_amount, crypto_price)

    If price retrieval fails:
        (None, None)
    """

    # Stablecoins
    if crypto in (
        "USDT TRC20",
        "USDT ERC20",
        "USDC ERC20",
    ):

        return amount, 1.0

    # BTC / ETH
    if crypto in ("BTC", "ETH"):

        price = get_live_crypto_price(crypto)

        if not price:
            return None, None

        crypto_amount = amount / price

        return crypto_amount, price

    return None, None


# ==========================================
# START WITHDRAWAL
# ==========================================

async def withdraw(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    status = get_kyc_status(user_id)

    if status != "Approved":

        await update.message.reply_text(
            "❌ Withdrawal Unavailable\n\n"
            "Your KYC verification has not been approved.\n\n"
            "You must complete KYC before requesting a withdrawal.",
            reply_markup=wallet_menu,
        )

        return ConversationHandler.END

    await update.message.reply_text(
        "💸 Withdrawal Request\n\n"
        "Select the cryptocurrency you want to withdraw.",
        reply_markup=withdraw_crypto_keyboard,
    )

    return CRYPTO


# ==========================================
# RECEIVE CRYPTO
# ==========================================

async def receive_crypto(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.message.text == "❌ Cancel":

        return await cancel(
            update,
            context,
        )

    crypto_map = {

        "₿ Withdraw BTC":
            "BTC",

        "♦ Withdraw ETH":
            "ETH",

        "💲 Withdraw USDT (TRC20)":
            "USDT TRC20",

        "💲 Withdraw USDT (ERC20)":
            "USDT ERC20",

        "💲 Withdraw USDC (ERC20)":
            "USDC ERC20",
    }

    selected = update.message.text

    if selected not in crypto_map:

        await update.message.reply_text(
            "❌ Please select a cryptocurrency "
            "using the buttons."
        )

        return CRYPTO

    crypto = crypto_map[selected]

    context.user_data["cryptocurrency"] = crypto

    await update.message.reply_text(
        "💰 Enter the withdrawal amount in USD.\n\n"
        "Example:\n"
        "100",
        reply_markup=cancel_menu,
    )

    return AMOUNT


# ==========================================
# RECEIVE AMOUNT
# ==========================================

async def receive_amount(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.message.text == "❌ Cancel":

        return await cancel(
            update,
            context,
        )

    # ==========================================
    # VALIDATE AMOUNT
    # ==========================================

    try:

        amount = float(
            update.message.text.strip()
        )

        if amount <= 0:
            raise ValueError

    except ValueError:

        await update.message.reply_text(
            "❌ Please enter a valid amount."
        )

        return AMOUNT

    # ==========================================
    # MINIMUM WITHDRAWAL
    # ==========================================

    if amount < 50:

        await update.message.reply_text(
            "❌ Minimum withdrawal is $50."
        )

        return AMOUNT

    # ==========================================
    # CHECK WALLET BALANCE
    # ==========================================

    balance = get_wallet_balance(
        update.effective_user.id
    )

    if balance < amount:

        await update.message.reply_text(
            f"❌ Insufficient wallet balance.\n\n"
            f"Available Balance: ${balance:,.2f}"
        )

        return AMOUNT

    crypto = context.user_data.get(
        "cryptocurrency"
    )

    if not crypto:

        await update.message.reply_text(
            "❌ Withdrawal session expired.\n\n"
            "Please start the withdrawal again.",
            reply_markup=wallet_menu,
        )

        return ConversationHandler.END

    # ==========================================
    # LIVE CONVERSION
    # ==========================================

    crypto_amount, crypto_price = (
        convert_usd_to_crypto(
            amount,
            crypto,
        )
    )

    # ==========================================
    # BTC / ETH PRICE UNAVAILABLE
    # ==========================================

    if crypto in ("BTC", "ETH"):

        if crypto_amount is None:

            await update.message.reply_text(
                "⚠️ Unable to retrieve the current "
                f"{crypto} market price.\n\n"
                "Please try again in a moment."
            )

            return AMOUNT

        await update.message.reply_text(
            "💱 *Withdrawal Conversion*\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"💵 USD Amount:\n"
            f"*${amount:,.2f}*\n\n"
            f"🪙 Current {crypto} Price:\n"
            f"*${crypto_price:,.2f}*\n\n"
            f"💰 Estimated {crypto} Amount:\n"
            f"*{crypto_amount:.8f} {crypto}*\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "The USD withdrawal amount is fixed.\n"
            "The crypto amount is calculated using "
            "the current live market price and may "
            "change as the market moves.",
            parse_mode="Markdown",
        )

    # ==========================================
    # USDT / USDC
    # ==========================================

    else:

        stablecoin_name = crypto.split()[0]

        await update.message.reply_text(
            "💸 Withdrawal Amount\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"💵 USD Amount:\n"
            f"*${amount:,.2f}*\n\n"
            f"💰 Estimated {stablecoin_name} Amount:\n"
            f"*{crypto_amount:.2f} {stablecoin_name}*\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Stablecoin conversion is calculated "
            "approximately 1:1 with USD.",
            parse_mode="Markdown",
        )

    # ==========================================
    # IMPORTANT
    #
    # Only USD amount is saved.
    # Crypto conversion is NOT saved in Supabase.
    # ==========================================

    context.user_data["amount"] = amount

    await update.message.reply_text(
        "📥 Enter your destination wallet address.",
        reply_markup=cancel_menu,
    )

    return ADDRESS


# ==========================================
# RECEIVE WALLET ADDRESS
# ==========================================

async def receive_address(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.message.text == "❌ Cancel":

        return await cancel(
            update,
            context,
        )

    wallet_address = update.message.text.strip()

    if not wallet_address:

        await update.message.reply_text(
            "❌ Wallet address cannot be empty."
        )

        return ADDRESS

    user_id = update.effective_user.id

    crypto = context.user_data.get(
        "cryptocurrency"
    )

    amount = context.user_data.get(
        "amount"
    )

    if not crypto or amount is None:

        await update.message.reply_text(
            "❌ Withdrawal session expired.\n\n"
            "Please start the withdrawal again.",
            reply_markup=wallet_menu,
        )

        return ConversationHandler.END

    # ==========================================
    # FINAL BALANCE CHECK
    # ==========================================

    balance = get_wallet_balance(
        user_id
    )

    if balance < amount:

        await update.message.reply_text(
            f"❌ Your wallet balance is no longer "
            f"sufficient for this withdrawal.\n\n"
            f"Available Balance: ${balance:,.2f}\n"
            f"Requested Amount: ${amount:,.2f}",
            reply_markup=wallet_menu,
        )

        context.user_data.pop(
            "cryptocurrency",
            None,
        )

        context.user_data.pop(
            "amount",
            None,
        )

        return ConversationHandler.END

    # ==========================================
    # SAVE WITHDRAWAL
    #
    # IMPORTANT:
    # `amount` is the USD amount.
    #
    # No BTC/ETH conversion amount is stored.
    # ==========================================

    result = create_withdrawal(
        user_id=user_id,
        cryptocurrency=crypto,
        wallet_address=wallet_address,
        amount=amount,
    )

    if not result:

        await update.message.reply_text(
            "❌ Failed to create the withdrawal request.\n\n"
            "Your wallet balance has not been changed.",
            reply_markup=wallet_menu,
        )

        return ConversationHandler.END

    # ==========================================
    # RESERVE / DEDUCT USD BALANCE
    # ==========================================

    admin_wallet_adjustment(
        user_id=user_id,
        amount=amount,
        transaction_type="Debit",
        reason="Withdrawal Request",
    )

    # ==========================================
    # RECORD TRANSACTION
    # ==========================================

    record_wallet_transaction(
        user_id=user_id,
        transaction_type="Withdrawal",
        amount=amount,
        reason="Withdrawal Pending Approval",
    )

    # ==========================================
    # GET CURRENT CONVERSION FOR CONFIRMATION
    #
    # This is display-only.
    # It is NOT saved to Supabase.
    # ==========================================

    crypto_amount, crypto_price = (
        convert_usd_to_crypto(
            amount,
            crypto,
        )
    )

    # ==========================================
    # USER CONFIRMATION
    # ==========================================

    if crypto in ("BTC", "ETH"):

        if crypto_amount is not None:

            conversion_text = (
                f"🪙 Current {crypto} Price: "
                f"${crypto_price:,.2f}\n"
                f"💰 Estimated Amount: "
                f"{crypto_amount:.8f} {crypto}\n\n"
            )

        else:

            conversion_text = (
                f"🪙 {crypto} Conversion: "
                "Currently unavailable\n\n"
            )

    else:

        stablecoin_name = crypto.split()[0]

        conversion_text = (
            f"💰 Estimated Amount: "
            f"{crypto_amount:.2f} "
            f"{stablecoin_name}\n\n"
        )

    await update.message.reply_text(
        "✅ *Withdrawal Request Submitted*\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"💵 USD Amount: *${amount:,.2f}*\n"
        f"🪙 Cryptocurrency: *{crypto}*\n\n"
        f"{conversion_text}"
        f"📥 Wallet Address:\n"
        f"`{wallet_address}`\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Your withdrawal request has been sent "
        "for administrator review.\n\n"
        "The USD amount has been reserved from "
        "your wallet.",
        parse_mode="Markdown",
        reply_markup=wallet_menu,
    )

    # ==========================================
    # ADMIN NOTIFICATION
    # ==========================================

    if crypto in ("BTC", "ETH"):

        if crypto_amount is not None:

            admin_conversion = (
                f"🪙 Current {crypto} Price: "
                f"${crypto_price:,.2f}\n"
                f"💰 Estimated {crypto}: "
                f"{crypto_amount:.8f} {crypto}\n\n"
            )

        else:

            admin_conversion = (
                f"🪙 {crypto} Conversion: "
                "Unavailable\n\n"
            )

    else:

        stablecoin_name = crypto.split()[0]

        admin_conversion = (
            f"💰 Estimated {stablecoin_name}: "
            f"{crypto_amount:.2f} {stablecoin_name}\n\n"
        )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "💸 *New Withdrawal Request*\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 User ID: `{user_id}`\n\n"
            f"🪙 Crypto: *{crypto}*\n"
            f"💵 USD Amount: *${amount:,.2f}*\n\n"
            f"{admin_conversion}"
            f"📥 Wallet Address:\n"
            f"`{wallet_address}`\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Status: ⏳ Pending Approval"
        ),
        parse_mode="Markdown",
    )

    # ==========================================
    # CLEAN SESSION
    # ==========================================

    context.user_data.pop(
        "cryptocurrency",
        None,
    )

    context.user_data.pop(
        "amount",
        None,
    )

    return ConversationHandler.END


# ==========================================
# CANCEL
# ==========================================

async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    context.user_data.pop(
        "cryptocurrency",
        None,
    )

    context.user_data.pop(
        "amount",
        None,
    )

    await update.message.reply_text(
        "Withdrawal cancelled.",
        reply_markup=wallet_menu,
    )

    return ConversationHandler.END


# ==========================================
# WITHDRAWAL HANDLER
# ==========================================

withdraw_handler = ConversationHandler(

    entry_points=[
        MessageHandler(
            filters.Regex(
                "^💸 Withdraw Funds$"
            ),
            withdraw,
        ),
    ],

    states={

        CRYPTO: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_crypto,
            ),
        ],

        AMOUNT: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_amount,
            ),
        ],

        ADDRESS: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_address,
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
