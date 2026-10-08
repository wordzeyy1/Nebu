from telegram import (
    Update,
    ReplyKeyboardMarkup,
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

from datetime import datetime
import asyncio
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from config import ADMIN_ID
from keyboards import main_menu

from database import (
    get_pending_kyc,
    get_pending_deposits,
    update_deposit_status,
    get_deposit,
    get_deposit_details,
    add_wallet_balance,
    record_wallet_transaction,
    get_pending_refunds,
    update_refund_status,
    get_refund,
    get_referrer,
    has_first_deposit,
    mark_first_deposit,
    add_referral_bonus,
    increment_referrals,
    get_pending_withdrawals,
    get_withdrawal,
    update_withdrawal_status,
    admin_wallet_adjustment,
)

from handlers.event_broadcast import (
    broadcast_deposit,
    broadcast_withdrawal,
    broadcast_refund,
)

# =====================================
# ADMIN MENU
# =====================================

admin_menu = ReplyKeyboardMarkup(
    [
        ["📥 Pending Deposits"],
        ["💸 Pending Withdrawals"],
        ["🪪 Change KYC Status"],
        ["🪪 Pending KYC"],
        ["💰 Pending Refunds"],
        ["⛏ Grant Mining Contract"],
        ["⛏ Terminate Mining Contract"],
        ["🚫 Ban User", "🔓 Unban User"],
        ["📨 Message User"],
        ["💳 Credit Wallet", "➖ Debit Wallet"],
        ["👥 Users", "📊 Statistics"],
        ["🏠 Main Menu"],
    ],
    resize_keyboard=True,
)


WITHDRAWAL_TXID = 0


# =====================================
# LIVE CRYPTO PRICE
# =====================================

def _fetch_crypto_price_sync(symbol: str):
    """
    Fetch current USD price from CoinGecko.

    This is synchronous internally and is executed with
    asyncio.to_thread() so it does not block the bot.
    """

    coin_ids = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
    }

    coin_id = coin_ids.get(symbol.upper())

    if not coin_id:
        return None

    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        f"?ids={coin_id}&vs_currencies=usd"
    )

    request = Request(
        url,
        headers={
            "User-Agent": "CryptoMines-Online-Bot/1.0",
            "Accept": "application/json",
        },
    )

    try:

        with urlopen(request, timeout=10) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        price = data.get(coin_id, {}).get("usd")

        if price is None:
            return None

        return float(price)

    except (
        HTTPError,
        URLError,
        TimeoutError,
        ValueError,
        KeyError,
        TypeError,
    ) as e:

        print(
            f"Failed to fetch {symbol} live price: {e}"
        )

        return None

    except Exception as e:

        print(
            f"Unexpected error fetching {symbol} price: {e}"
        )

        return None


async def get_live_crypto_price(symbol: str):
    """
    Async wrapper around the live price request.
    """

    return await asyncio.to_thread(
        _fetch_crypto_price_sync,
        symbol,
    )


# =====================================
# CALCULATE CRYPTO AMOUNT
# =====================================

async def calculate_withdrawal_crypto_amount(
    cryptocurrency,
    usd_amount,
):
    """
    Calculate the current crypto quantity for the
    USD withdrawal amount.

    Nothing is stored in the database.

    BTC/ETH:
        USD amount / current market price

    USDT/USDC:
        Approximately 1 USD per token.
    """

    crypto_name = cryptocurrency.upper()

    # ---------------------------------
    # BTC
    # ---------------------------------

    if crypto_name == "BTC":

        price = await get_live_crypto_price("BTC")

        if not price or price <= 0:
            return None, None

        crypto_amount = usd_amount / price

        return crypto_amount, price

    # ---------------------------------
    # ETH
    # ---------------------------------

    if crypto_name == "ETH":

        price = await get_live_crypto_price("ETH")

        if not price or price <= 0:
            return None, None

        crypto_amount = usd_amount / price

        return crypto_amount, price

    # ---------------------------------
    # USDT / USDC
    # ---------------------------------

    if crypto_name.startswith("USDT"):

        return usd_amount, 1.00

    if crypto_name.startswith("USDC"):

        return usd_amount, 1.00

    return None, None


# =====================================
# ADMIN PANEL
# =====================================

async def admin_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ Unauthorized.",
            reply_markup=main_menu,
        )

        return

    await update.message.reply_text(
        "🛠 *Admin Dashboard*\n\n"
        "Select an option below.",
        parse_mode="Markdown",
        reply_markup=admin_menu,
    )


# =====================================
# PENDING KYC
# =====================================

async def pending_kyc(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:
        return

    kycs = get_pending_kyc()

    if not kycs:

        await update.message.reply_text(
            "✅ There are no pending KYC submissions."
        )

        return

    for kyc in kycs:

        user_id = kyc[0]
        full_name = kyc[1]
        id_document = kyc[2]
        selfie = kyc[3]

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Approve",
                        callback_data=f"approve_kyc:{user_id}",
                    ),
                    InlineKeyboardButton(
                        "❌ Reject",
                        callback_data=f"reject_kyc:{user_id}",
                    ),
                ]
            ]
        )

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=id_document,
            caption=(
                f"🪪 Pending KYC\n\n"
                f"👤 {full_name}\n"
                f"🆔 {user_id}\n\n"
                "📄 Identity Document"
            ),
            reply_markup=keyboard,
        )

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=selfie,
            caption="🤳 Selfie Holding Identity Document",
        )


# =====================================
# PENDING DEPOSITS
# =====================================

async def pending_deposits(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:
        return

    deposits = get_pending_deposits()

    if not deposits:

        await update.message.reply_text(
            "No pending deposits."
        )

        return

    for deposit in deposits:

        deposit_id = deposit[0]
        user_id = deposit[1]
        network = deposit[2]
        amount = deposit[3]
        crypto_amount = deposit[4]
        txid = deposit[5]

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Approve",
                        callback_data=f"approve_deposit:{deposit_id}",
                    ),
                    InlineKeyboardButton(
                        "❌ Reject",
                        callback_data=f"reject_deposit:{deposit_id}",
                    ),
                ]
            ]
        )

        await update.message.reply_text(
            f"📥 *Pending Deposit*\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"🌐 Network: {network}\n"
            f"💵 USD: ${amount:,.2f}\n"
            f"🪙 Crypto: {crypto_amount}\n\n"
            f"🔗 TXID:\n`{txid}`",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


# =====================================
# PENDING REFUNDS
# =====================================

async def pending_refunds(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:
        return

    refunds = get_pending_refunds()

    if not refunds:

        await update.message.reply_text(
            "No pending refunds."
        )

        return

    for refund in refunds:

        refund_id = refund[0]
        user_id = refund[1]
        full_name = refund[2]
        investment_amount = refund[5]
        cryptocurrency = refund[6]

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Approve",
                        callback_data=f"approve_refund:{refund_id}",
                    ),
                    InlineKeyboardButton(
                        "❌ Reject",
                        callback_data=f"reject_refund:{refund_id}",
                    ),
                ]
            ]
        )

        await update.message.reply_text(
            f"💰 *Pending Refund*\n\n"
            f"👤 {full_name}\n"
            f"🆔 User ID: `{user_id}`\n"
            f"💵 Amount: {investment_amount}\n"
            f"🪙 Crypto: {cryptocurrency}",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


# =====================================
# PENDING WITHDRAWALS
# =====================================

async def pending_withdrawals(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:
        return

    withdrawals = get_pending_withdrawals()

    if not withdrawals:

        await update.message.reply_text(
            "✅ No pending withdrawal requests."
        )

        return

    for withdrawal in withdrawals:

        withdrawal_id = withdrawal[0]
        user_id = withdrawal[1]
        cryptocurrency = withdrawal[2]
        wallet_address = withdrawal[3]
        amount = withdrawal[4]

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Approve",
                        callback_data=f"approve_withdrawal:{withdrawal_id}",
                    ),
                    InlineKeyboardButton(
                        "❌ Reject",
                        callback_data=f"reject_withdrawal:{withdrawal_id}",
                    ),
                ]
            ]
        )

        await update.message.reply_text(
            f"💸 *Pending Withdrawal*\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"🪙 Cryptocurrency: {cryptocurrency}\n"
            f"💵 Amount: ${amount:,.2f}\n\n"
            f"📥 Wallet Address:\n"
            f"`{wallet_address}`",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


# =====================================
# DEPOSIT CALLBACK
# =====================================

async def deposit_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    action, deposit_id = query.data.split(":")
    deposit_id = int(deposit_id)

    if action == "approve_deposit":

        update_deposit_status(
            deposit_id,
            "Approved",
        )

        deposit_details = get_deposit_details(
            deposit_id
        )

        if not deposit_details:
            await query.edit_message_text(
                "❌ Deposit could not be found."
            )
            return

        user_id, amount, crypto_amount, network = deposit_details

        add_wallet_balance(
            user_id,
            amount,
        )

        record_wallet_transaction(
            user_id=user_id,
            transaction_type="Deposit",
            amount=amount,
            reason="Crypto Deposit Approved",
        )
        await broadcast_deposit(
            bot=context.bot,
            user_id=user_id,
            network=network,
            usd_amount=float(amount),
            crypto_amount=float(crypto_amount),
        )

        # =====================================
        # FIRST DEPOSIT REFERRAL BONUS
        # =====================================

        if not has_first_deposit(user_id):

            mark_first_deposit(user_id)

            referrer_id = get_referrer(user_id)

            if referrer_id:

                increment_referrals(
                    referrer_id
                )

                bonus = round(
                    amount * 0.10,
                    2,
                )

                add_referral_bonus(
                    referrer_id,
                    bonus,
                )

                record_wallet_transaction(
                    user_id=referrer_id,
                    transaction_type="Referral Bonus",
                    amount=bonus,
                    reason="10% First Deposit Referral Bonus",
                )

                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=(
                        "🎉 *Referral Bonus Earned!*\n\n"
                        "One of your direct referrals has "
                        "completed their first verified deposit.\n\n"
                        f"💰 Bonus Earned: *${bonus:,.2f}*\n\n"
                        "The bonus has been credited to your "
                        "Affiliate Balance.\n\n"
                        "⚠️ Referral bonuses cannot be withdrawn "
                        "immediately.\n"
                        "They must first be used to purchase "
                        "Cloud Mining hash power."
                    ),
                    parse_mode="Markdown",
                )

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"✅ Your deposit of ${amount:,.2f} "
                "has been approved.\n\n"
                "The funds have been added to your wallet."
            ),
        )

        await query.edit_message_text(
            "✅ Deposit Approved"
        )

    elif action == "reject_deposit":

        update_deposit_status(
            deposit_id,
            "Rejected",
        )

        user_id, amount = get_deposit(
            deposit_id
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"❌ Your deposit of ${amount:,.2f} "
                "has been rejected."
            ),
        )

        await query.edit_message_text(
            "❌ Deposit Rejected"
        )


# =====================================
# REFUND CALLBACK
# =====================================

async def refund_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    action, refund_id = query.data.split(":")
    refund_id = int(refund_id)

    user_id, amount = get_refund(
        refund_id
    )

    amount = float(
        str(amount)
        .replace("$", "")
        .replace(",", "")
        .strip()
    )

    if action == "approve_refund":

        update_refund_status(
            refund_id,
            "Approved",
        )

        add_wallet_balance(
            user_id,
            amount,
        )

        record_wallet_transaction(
            user_id=user_id,
            transaction_type="Refund",
            amount=amount,
            reason="Refund Approved",
        )
        
        await broadcast_refund(
            bot=context.bot,
            user_id=user_id,
            refund_amount=amount,
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "✅ Your refund request has been approved.\n\n"
                f"${amount:,.2f} has been added to your wallet."
            ),
        )

        await query.edit_message_text(
            "✅ Refund Approved"
        )

    elif action == "reject_refund":

        update_refund_status(
            refund_id,
            "Rejected",
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ Your refund request has been rejected."
            ),
        )

        await query.edit_message_text(
            "❌ Refund Rejected"
        )


# =====================================
# WITHDRAWAL CALLBACK
# =====================================

async def withdrawal_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return ConversationHandler.END

    action, withdrawal_id = query.data.split(":")
    withdrawal_id = int(withdrawal_id)

    withdrawal = get_withdrawal(
        withdrawal_id
    )

    if not withdrawal:

        await query.edit_message_text(
            "❌ Withdrawal request no longer exists."
        )

        return ConversationHandler.END

    user_id, amount, cryptocurrency, wallet_address = withdrawal

    # =====================================
    # APPROVE
    # =====================================

    if action == "approve_withdrawal":

        context.user_data["withdrawal_id"] = withdrawal_id

        await query.message.reply_text(
            "📤 *Complete Withdrawal*\n\n"
            "Paste the blockchain Transaction Hash (TXID).\n\n"
            "Example:\n"
            "`5f94cb65ad77f4d7...`",
            parse_mode="Markdown",
        )

        await query.edit_message_text(
            "⏳ Withdrawal approved for processing.\n\n"
            "Waiting for blockchain TXID..."
        )

        return WITHDRAWAL_TXID

    # =====================================
    # REJECT
    # =====================================

    elif action == "reject_withdrawal":

        reason = (
            "Withdrawal rejected by administrator."
        )

        update_withdrawal_status(
            withdrawal_id,
            "Rejected",
            reason,
        )

        # Return reserved funds
        admin_wallet_adjustment(
            user_id=user_id,
            amount=amount,
            transaction_type="Credit",
            reason="Rejected Withdrawal Refund",
        )

        record_wallet_transaction(
            user_id=user_id,
            transaction_type="Withdrawal",
            amount=amount,
            reason="Withdrawal Rejected (Refunded)",
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ *Withdrawal Rejected*\n\n"
                f"💵 Amount: ${amount:,.2f}\n"
                f"🪙 Network: {cryptocurrency}\n\n"
                f"Reason:\n{reason}\n\n"
                "The amount has been returned to your wallet."
            ),
            parse_mode="Markdown",
        )

        await query.edit_message_text(
            "❌ Withdrawal Rejected"
        )

        return ConversationHandler.END


# =====================================
# RECEIVE WITHDRAWAL TXID
# =====================================

async def receive_withdrawal_txid(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    txid = update.message.text.strip()

    if not txid:

        await update.message.reply_text(
            "❌ Please enter a valid transaction hash."
        )

        return WITHDRAWAL_TXID

    withdrawal_id = context.user_data.get(
        "withdrawal_id"
    )

    if not withdrawal_id:

        await update.message.reply_text(
            "❌ Withdrawal session expired. "
            "Please open Pending Withdrawals again.",
            reply_markup=admin_menu,
        )

        context.user_data.clear()

        return ConversationHandler.END

    withdrawal = get_withdrawal(
        withdrawal_id
    )

    if not withdrawal:

        await update.message.reply_text(
            "❌ Withdrawal request could not be found.",
            reply_markup=admin_menu,
        )

        context.user_data.clear()

        return ConversationHandler.END

    user_id, amount, cryptocurrency, wallet_address = withdrawal

    # Ensure numeric USD value
    amount = float(amount)

    # =====================================
    # GET CURRENT LIVE CRYPTO PRICE
    # =====================================

    crypto_amount, current_price = (
        await calculate_withdrawal_crypto_amount(
            cryptocurrency,
            amount,
        )
    )

    # =====================================
    # UPDATE DATABASE
    # =====================================

    update_withdrawal_status(
        withdrawal_id=withdrawal_id,
        status="Approved",
        txid=txid,
        completed_at=datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    )

    record_wallet_transaction(
        user_id=user_id,
        transaction_type="Withdrawal",
        amount=amount,
        reason="Withdrawal Approved",
    )

    await broadcast_withdrawal(
        bot=context.bot,
        user_id=user_id,
        cryptocurrency=cryptocurrency,
        usd_amount=amount,
        crypto_amount=crypto_amount,
    )

    # =====================================
    # BUILD CRYPTO DISPLAY
    # =====================================

    crypto_display = ""

    if crypto_amount is not None:

        if cryptocurrency == "BTC":

            crypto_display = (
                f"₿ BTC Price at Completion: "
                f"${current_price:,.2f}\n"
                f"🪙 BTC Amount: "
                f"{crypto_amount:.8f} BTC\n"
            )

        elif cryptocurrency == "ETH":

            crypto_display = (
                f"♦ ETH Price at Completion: "
                f"${current_price:,.2f}\n"
                f"🪙 ETH Amount: "
                f"{crypto_amount:.8f} ETH\n"
            )

        elif cryptocurrency.startswith("USDT"):

            crypto_display = (
                f"🪙 USDT Amount: "
                f"{crypto_amount:,.2f} USDT\n"
            )

        elif cryptocurrency.startswith("USDC"):

            crypto_display = (
                f"🪙 USDC Amount: "
                f"{crypto_amount:,.2f} USDC\n"
            )

    else:

        crypto_display = (
            f"🪙 Crypto Amount: "
            "Current market price unavailable.\n"
        )

    # =====================================
    # FINAL USER NOTIFICATION
    # =====================================

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "✅ *Withdrawal Completed*\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"💵 USD Amount: "
            f"${amount:,.2f}\n"
            f"🌐 Network: {cryptocurrency}\n\n"
            f"{crypto_display}\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"📥 *Destination Wallet:*\n"
            f"`{wallet_address}`\n\n"
            f"🔗 *Transaction Hash:*\n"
            f"`{txid}`\n\n"
            "Your withdrawal has been broadcast "
            "to the blockchain.\n\n"
            "Network confirmations may take a few minutes.\n\n"
            "ℹ️ The USD amount is fixed. "
            "The displayed crypto amount is calculated "
            "using the current market price at completion."
        ),
        parse_mode="Markdown",
    )

    await update.message.reply_text(
        "✅ Withdrawal completed successfully.",
        reply_markup=admin_menu,
    )

    context.user_data.clear()

    return ConversationHandler.END


# =====================================
# HANDLERS
# =====================================

admin_panel_handler = MessageHandler(
    filters.Regex("^🛠 Admin Panel$"),
    admin_panel,
)


pending_kyc_handler = MessageHandler(
    filters.Regex("^🪪 Pending KYC$"),
    pending_kyc,
)


pending_deposits_handler = MessageHandler(
    filters.Regex("^📥 Pending Deposits$"),
    pending_deposits,
)


pending_withdrawals_handler = MessageHandler(
    filters.Regex("^💸 Pending Withdrawals$"),
    pending_withdrawals,
)


pending_refunds_handler = MessageHandler(
    filters.Regex("^💰 Pending Refunds$"),
    pending_refunds,
)


deposit_callback_handler = CallbackQueryHandler(
    deposit_callback,
    pattern=r"^(approve_deposit|reject_deposit):",
)


refund_callback_handler = CallbackQueryHandler(
    refund_callback,
    pattern=r"^(approve_refund|reject_refund):",
)


# =====================================
# WITHDRAWAL CONVERSATION
# =====================================

withdrawal_handler = ConversationHandler(

    entry_points=[
        CallbackQueryHandler(
            withdrawal_callback,
            pattern=r"^(approve_withdrawal|reject_withdrawal):",
        )
    ],

    states={

        WITHDRAWAL_TXID: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_withdrawal_txid,
            )
        ],

    },

    fallbacks=[],

)
