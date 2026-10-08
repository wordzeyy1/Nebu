from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)

from config import ADMIN_ID

from database import (
    get_admin_users,
    get_admin_statistics,
)

# Use the existing admin menu from admin_panel.py.
#
# This avoids creating a second copy of the menu.
from handlers.admin_panel import admin_menu


# =====================================
# USERS
# =====================================

async def admin_users(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    if update.effective_user.id != ADMIN_ID:

        if update.message:
            await update.message.reply_text(
                "❌ Access denied."
            )

        return

    try:

        users = get_admin_users()

    except Exception as exc:

        print(
            f"❌ Failed to load admin users: {exc}"
        )

        await update.message.reply_text(
            "❌ Failed to load users.\n\n"
            "Please try again.",
            reply_markup=admin_menu,
        )

        return

    if not users:

        await update.message.reply_text(
            "👥 *Users*\n\n"
            "No registered users found.",
            parse_mode="Markdown",
            reply_markup=admin_menu,
        )

        return

    # =================================
    # HEADER
    # =================================

    lines = [
        "👥 *Registered Users*",
        "",
        f"👤 Total shown: *{len(users)}*",
        "",
        "━━━━━━━━━━━━━━━━━━",
        "",
    ]

    # =================================
    # USERS
    # =================================

    for index, user in enumerate(
        users,
        start=1,
    ):

        user_id = user.get(
            "user_id"
        )

        full_name = (
            user.get("full_name")
            or "Unknown User"
        )

        kyc_status = (
            user.get("kyc_status")
            or "Pending"
        )

        wallet_balance = float(
            user.get("wallet_balance") or 0
        )

        referrals = int(
            user.get("referrals") or 0
        )

        is_banned = bool(
            user.get(
                "is_banned",
                False,
            )
        )

        if is_banned:
            account_status = "🚫 BANNED"
        else:
            account_status = "✅ Active"

        lines.append(
            f"*{index}. {full_name}*"
        )

        lines.append(
            f"🆔 `{user_id}`"
        )

        lines.append(
            f"🪪 KYC: {kyc_status}"
        )

        lines.append(
            f"💼 Wallet: "
            f"${wallet_balance:,.2f}"
        )

        lines.append(
            f"👥 Referrals: {referrals}"
        )

        lines.append(
            f"🔐 Status: {account_status}"
        )

        lines.append("")

        lines.append(
            "━━━━━━━━━━━━━━━━━━"
        )

        lines.append("")

    text = "\n".join(lines)

    # =================================
    # TELEGRAM MESSAGE LIMIT
    # =================================

    chunks = []

    while len(text) > 3800:

        split_at = text.rfind(
            "\n",
            0,
            3800,
        )

        if split_at <= 0:
            split_at = 3800

        chunks.append(
            text[:split_at]
        )

        text = text[split_at:].lstrip()

    if text:
        chunks.append(text)

    # =================================
    # SEND
    # =================================

    for chunk in chunks:

        await update.message.reply_text(
            chunk,
            parse_mode="Markdown",
        )

    await update.message.reply_text(
        "🛠 *Admin Dashboard*\n\n"
        "Select an option below.",
        parse_mode="Markdown",
        reply_markup=admin_menu,
    )


# =====================================
# STATISTICS
# =====================================

async def admin_statistics(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    if update.effective_user.id != ADMIN_ID:

        if update.message:
            await update.message.reply_text(
                "❌ Access denied."
            )

        return

    try:

        stats = get_admin_statistics()

    except Exception as exc:

        print(
            f"❌ Failed to load statistics: {exc}"
        )

        await update.message.reply_text(
            "❌ Failed to load statistics.\n\n"
            "Please try again.",
            reply_markup=admin_menu,
        )

        return

    total_users = stats[
        "total_users"
    ]

    banned_users = stats[
        "banned_users"
    ]

    active_users = max(
        total_users - banned_users,
        0,
    )

    wallet_balance = stats[
        "total_wallet_balance"
    ]

    affiliate_balance = stats[
        "total_affiliate_balance"
    ]

    active_contracts = stats[
        "active_mining_contracts"
    ]

    total_hash_power = stats[
        "total_hash_power"
    ]

    daily_income = stats[
        "daily_mining_income"
    ]

    pending_kyc = stats[
        "pending_kyc"
    ]

    pending_deposits = stats[
        "pending_deposits"
    ]

    pending_withdrawals = stats[
        "pending_withdrawals"
    ]

    pending_refunds = stats[
        "pending_refunds"
    ]

    # =================================
    # MESSAGE
    # =================================

    text = (
        "📊 *NebuMine Pro Statistics*\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "👥 *USERS*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"👤 Total Users: "
        f"*{total_users:,}*\n"

        f"✅ Active Users: "
        f"*{active_users:,}*\n"

        f"🚫 Banned Users: "
        f"*{banned_users:,}*\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "💰 *WALLET*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"💼 Total Wallet Balance: "
        f"*${wallet_balance:,.2f}*\n"

        f"🤝 Total Affiliate Balance: "
        f"*${affiliate_balance:,.2f}*\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "⛏ *MINING*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"⛏ Active Contracts: "
        f"*{active_contracts:,}*\n"

        f"⚡ Total Hash Power: "
        f"*{total_hash_power:,.2f}*\n"

        f"💵 Daily Mining Income: "
        f"*${daily_income:,.2f}*\n"

        f"📅 Estimated 30-Day Income: "
        f"*${daily_income * 30:,.2f}*\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "⏳ *PENDING ITEMS*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"🪪 Pending KYC: "
        f"*{pending_kyc:,}*\n"

        f"📥 Pending Deposits: "
        f"*{pending_deposits:,}*\n"

        f"💸 Pending Withdrawals: "
        f"*{pending_withdrawals:,}*\n"

        f"💰 Pending Refunds: "
        f"*{pending_refunds:,}*\n\n"

        "━━━━━━━━━━━━━━━━━━"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=admin_menu,
    )


# =====================================
# USERS HANDLER
# =====================================

admin_users_handler = MessageHandler(
    filters.Regex(
        r"^👥 Users$"
    ),
    admin_users,
)


# =====================================
# STATISTICS HANDLER
# =====================================

admin_statistics_handler = MessageHandler(
    filters.Regex(
        r"^📊 Statistics$"
    ),
    admin_statistics,
)
