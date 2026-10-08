import os

from telegram import Bot

from utils.rolling_broadcast import send_rolling_broadcast


EVENT_BROADCAST_CHANNEL = os.getenv(
    "EVENT_BROADCAST_CHANNEL"
)


# =====================================
# MEMBER LABEL
# =====================================

def _member_label(user_id: int) -> str:
    """
    Public-facing member identifier.

    We deliberately do not expose the real Telegram user ID.
    """

    return f"Member #{str(user_id)[-4:]}"


# =====================================
# SEND EVENT
# =====================================

async def _send_event(
    bot: Bot,
    text: str,
    event_type: str,
):
    """
    Send an event announcement to the public channel
    using the rolling-broadcast system.

    Each event type keeps only the latest 7 messages.

    Broadcasting is deliberately fail-safe:
    a Telegram/channel failure must never interrupt
    the underlying financial/database operation.
    """

    if not EVENT_BROADCAST_CHANNEL:

        print(
            "EVENT_BROADCAST_CHANNEL is not configured. "
            "Skipping event broadcast."
        )

        return False

    try:

        await send_rolling_broadcast(
            bot=bot,
            chat_id=EVENT_BROADCAST_CHANNEL,
            text=text,
            event_type=event_type,
            parse_mode="HTML",
        )

        return True

    except Exception as exc:

        print(
            "Event broadcast failed: "
            f"{type(exc).__name__}: {exc}"
        )

        return False


# =====================================
# CONTRACT PURCHASE
# =====================================

async def broadcast_contract_purchase(
    bot: Bot,
    user_id: int,
    hash_power: float,
    investment: float,
    daily_earnings: float,
):
    """
    Broadcast a newly activated mining contract.
    """

    member = _member_label(user_id)

    text = (
        "⛏️ <b>NEW MINING CONTRACT</b>\n\n"
        f"👤 {member}\n\n"
        f"⚡ Hash Power: "
        f"<b>{hash_power:,.2f} TH/s</b>\n"
        f"💰 Investment: "
        f"<b>${investment:,.2f}</b>\n"
        f"📈 Daily Earnings: "
        f"<b>${daily_earnings:,.2f}</b>\n\n"
        "✅ Contract Activated"
    )

    return await _send_event(
        bot=bot,
        text=text,
        event_type="contract_purchase",
    )


# =====================================
# DEPOSIT
# =====================================

async def broadcast_deposit(
    bot: Bot,
    user_id: int,
    network: str,
    usd_amount: float,
    crypto_amount: float,
):
    """
    Broadcast an approved deposit.
    """

    member = _member_label(user_id)

    crypto_text = f"{crypto_amount:,.8f}"

    # Stablecoins look better with 2 decimals.
    if (
        network.startswith("USDT")
        or network.startswith("USDC")
    ):
        crypto_text = f"{crypto_amount:,.2f}"

    symbol = network.split()[0]

    text = (
        "💰 <b>DEPOSIT CONFIRMED</b>\n\n"
        f"👤 {member}\n\n"
        f"🌐 Network: <b>{network}</b>\n"
        f"💵 Deposit: <b>${usd_amount:,.2f}</b>\n"
        f"🪙 Amount: "
        f"<b>{crypto_text} {symbol}</b>\n\n"
        "✅ Deposit Approved"
    )

    return await _send_event(
        bot=bot,
        text=text,
        event_type="deposit",
    )


# =====================================
# WITHDRAWAL
# =====================================

async def broadcast_withdrawal(
    bot: Bot,
    user_id: int,
    cryptocurrency: str,
    usd_amount: float,
    crypto_amount: float | None,
):
    """
    Broadcast a completed withdrawal.

    Never exposes the destination wallet or TXID.
    """

    member = _member_label(user_id)

    if crypto_amount is None:

        crypto_text = "Amount unavailable"

    elif cryptocurrency.upper() in (
        "BTC",
        "ETH",
    ):

        crypto_text = f"{crypto_amount:,.8f}"

    else:

        crypto_text = f"{crypto_amount:,.2f}"

    symbol = cryptocurrency.split()[0].upper()

    text = (
        "📤 <b>WITHDRAWAL COMPLETED</b>\n\n"
        f"👤 {member}\n\n"
        f"🌐 Network: "
        f"<b>{cryptocurrency}</b>\n"
        f"💵 Amount: "
        f"<b>${usd_amount:,.2f}</b>\n"
        f"🪙 Sent: "
        f"<b>{crypto_text} {symbol}</b>\n\n"
        "✅ Withdrawal Completed"
    )

    return await _send_event(
        bot=bot,
        text=text,
        event_type="withdrawal",
    )


# =====================================
# MINING REWARD
# =====================================

async def broadcast_mining_reward(
    bot: Bot,
    user_id: int,
    reward_amount: float,
):
    """
    Broadcast a successfully claimed mining reward.
    """

    member = _member_label(user_id)

    text = (
        "🎁 <b>MINING REWARD CLAIMED</b>\n\n"
        f"👤 {member}\n\n"
        f"💰 Reward: "
        f"<b>${reward_amount:,.2f}</b>\n\n"
        "✅ Credited to Wallet"
    )

    return await _send_event(
        bot=bot,
        text=text,
        event_type="mining_reward",
    )


# =====================================
# REFUND
# =====================================

async def broadcast_refund(
    bot: Bot,
    user_id: int,
    refund_amount: float,
):
    """
    Broadcast an approved refund.

    No refund ID or private user information is exposed.
    """

    member = _member_label(user_id)

    text = (
        "💰 <b>REFUND APPROVED</b>\n\n"
        f"👤 {member}\n\n"
        f"💵 Refund: "
        f"<b>${refund_amount:,.2f}</b>\n\n"
        "✅ Credited to Wallet"
    )

    return await _send_event(
        bot=bot,
        text=text,
        event_type="refund",
    )
