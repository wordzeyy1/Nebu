from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from datetime import time, timezone

from config import BOT_TOKEN, ADMIN_ID

from database import create_tables

from keyboards import (
    main_menu,
    admin_menu,
)

from handlers.main_menu import (
    show_main_menu,
    main_menu_handler,
)

# =====================================
# GLOBAL BAN GUARD
# =====================================

from handlers.ban_guard import (
    global_ban_check,
)

# =====================================
# USER HANDLERS
# =====================================

from handlers.registration import (
    registration_handler,
)

from handlers.profile import (
    profile_handler,
)

from handlers.wallet import (
    wallet,
    wallet_handler,
)

from handlers.fund_wallet import (
    fund_wallet,
    fund_wallet_handler,
)

from handlers.deposit import (
    deposit_handler,
    select_btc,
)

from handlers.submit_tx import (
    submit_tx_handler,
)

from handlers.history import (
    history_handler,
    withdrawal_history_handler,
)

from handlers.referrals import (
    referral_handler,
)

from handlers.refund import (
    refund_handler,
)

from handlers.check_status import (
    check_status_handler,
)

from handlers.help import (
    help_handler,
)

from handlers.faq import (
    faq_handler,
)

from handlers.terms import (
    terms_handler,
)

from handlers.privacy import (
    privacy_handler,
)

from handlers.page_registry import (
    register_page,
)

from handlers.navigation import (
    clear_navigation,
    push_page,
    back_handler,
)

from handlers.withdraw import (
    withdraw_handler,
)

from handlers.change_withdrawal_address import (
    change_withdrawal_address_handler,
)

# =====================================
# ADMIN WALLET / CONTRACT
# =====================================

from handlers.admin_wallet import (
    admin_wallet_handler,
)

from handlers.admin_contract import (
    admin_contract_handler,
)

from handlers.admin_contract_termination import (
    admin_contract_termination_handler,
)

# =====================================
# ADMIN BAN / UNBAN
# =====================================

from handlers.admin_ban import (
    ban_user_handler,
    unban_user_handler,
)

# =====================================
# ADMIN USERS / STATISTICS
# =====================================

from handlers.admin_users_stats import (
    admin_users_handler,
    admin_statistics_handler,
)

# =====================================
# CRYPTO MARKET BROADCAST
# =====================================

from handlers.crypto_broadcast import (
    crypto_broadcast_job,
)

# =====================================
# ADMIN MESSAGE
# =====================================

from handlers.admin_message import (
    admin_message_handler,
    user_reply_handler,
)

# =====================================
# CLOUD MINING
# =====================================

from handlers.mining import (
    mining_handler,
    buy_hashpower_handler,
    claim_rewards_handler,
    contracts_handler,
)

# =====================================
# SUPPORT
# =====================================

from handlers.vip_support import (
    vip_support_handler,
    vip_support_main_menu_handler,
)

from handlers.support_reply import (
    reply_handler,
)

# =====================================
# KYC
# =====================================

from handlers.kyc import (
    kyc_handler,
    kyc_status,
)

from handlers.kyc_admin import (
    approve_kyc_handler,
    reject_kyc_handler,
    kyc_callback_handler,
)

from handlers.admin_kyc_status import (
    admin_kyc_status_handler,
    manual_kyc_status_callback_handler,
)

# =====================================
# ADMIN PANEL
# =====================================

from handlers.admin_panel import (
    admin_panel_handler,
    pending_kyc_handler,
    pending_deposits_handler,
    pending_withdrawals_handler,
    pending_refunds_handler,
    deposit_callback_handler,
    refund_callback_handler,
    withdrawal_handler,
)


# =====================================
# START
# =====================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    # Reset navigation whenever /start is used.
    clear_navigation(context)

    if context.args:

        try:
            context.user_data["referrer_id"] = int(
                context.args[0]
            )

        except ValueError:
            pass

    await show_main_menu(
        update,
        context,
    )


# =====================================
# MENU COMMAND
# =====================================

async def menu_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    clear_navigation(context)

    await show_main_menu(
        update,
        context,
    )


# =====================================
# HELP COMMAND
# =====================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        "ℹ️ NebuMine Pro Bot\n\n"
        "Use the menu buttons to access the available features."
    )


# =====================================
# GLOBAL MENU BUTTONS
# =====================================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return

    text = update.message.text

    # ---------------------------------
    # MAIN MENU
    # ---------------------------------

    if text == "🏠 Main Menu":

        clear_navigation(context)

        await show_main_menu(
            update,
            context,
        )

        return

    # ---------------------------------
    # KYC STATUS
    # ---------------------------------

    if text == "🪪 KYC Status":

        await kyc_status(
            update,
            context,
        )

        return

    # ---------------------------------
    # WALLET
    # ---------------------------------

    if text == "💼 Wallet":

        await wallet(
            update,
            context,
        )

        return

    # ---------------------------------
    # ADMIN PANEL
    # ---------------------------------

    if text == "🛠 Admin Panel":

        if update.effective_user.id != ADMIN_ID:

            await update.message.reply_text(
                "❌ Access denied."
            )

            return

        # The actual admin_panel_handler handles
        # the Admin Panel button.
        return


# =====================================
# MAIN
# =====================================

def main():

    # =================================
    # DATABASE
    # =================================

    create_tables()

    # =================================
    # APPLICATION
    # =================================

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # =====================================
    # GLOBAL BAN GUARD
    # =====================================
    #
    # IMPORTANT:
    #
    # The guard runs in group -1, before
    # normal handlers in group 0.
    #
    # If the user is banned,
    # global_ban_check raises
    # ApplicationHandlerStop and prevents
    # the update from reaching the rest
    # of the bot.
    # =====================================

    app.add_handler(
        MessageHandler(
            filters.ALL,
            global_ban_check,
        ),
        group=-1,
    )

    app.add_handler(
        CallbackQueryHandler(
            global_ban_check,
        ),
        group=-1,
    )

    # =====================================
    # SLASH COMMANDS
    # =====================================

    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    app.add_handler(
        CommandHandler(
            "help",
            help_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "menu",
            menu_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "wallet",
            wallet,
        )
    )

    # =====================================
    # GLOBAL NAVIGATION
    # =====================================
    #
    # These are registered before the
    # ConversationHandlers.
    # =====================================

    menu_filter = filters.Regex(
        r"^(🏠 Main Menu|💼 Wallet|🪪 KYC Status)$"
    )

    app.add_handler(
        MessageHandler(
            menu_filter,
            buttons,
        )
    )

    # =====================================
    # UNIVERSAL BACK BUTTON
    # =====================================

    app.add_handler(
        back_handler
    )

    # =====================================
    # NORMAL TOP-LEVEL USER HANDLERS
    # =====================================

    app.add_handler(
        profile_handler
    )

    app.add_handler(
        wallet_handler
    )

    app.add_handler(
        fund_wallet_handler
    )

    app.add_handler(
        history_handler
    )

    app.add_handler(
        withdrawal_history_handler
    )

    app.add_handler(
        referral_handler
    )

    app.add_handler(
        check_status_handler
    )

    # =====================================
    # CLOUD MINING
    # =====================================

    app.add_handler(
        mining_handler
    )

    app.add_handler(
        buy_hashpower_handler
    )

    app.add_handler(
        claim_rewards_handler
    )

    app.add_handler(
        contracts_handler
    )

    # =====================================
    # SUPPORT
    # =====================================

    app.add_handler(
        vip_support_handler
    )

    app.add_handler(
        vip_support_main_menu_handler
    )

    app.add_handler(
        reply_handler
    )

    # =====================================
    # ADMIN PANEL
    # =====================================

    app.add_handler(
        admin_users_handler
    )

    app.add_handler(
        admin_statistics_handler
    )

    app.add_handler(
        admin_panel_handler
    )

    app.add_handler(
        pending_kyc_handler
    )

    app.add_handler(
        pending_deposits_handler
    )

    app.add_handler(
        pending_withdrawals_handler
    )

    app.add_handler(
        pending_refunds_handler
    )

    app.add_handler(
        deposit_callback_handler
    )

    app.add_handler(
        refund_callback_handler
    )

    app.add_handler(
        withdrawal_handler
    )

    # =====================================
    # ADMIN WALLET / CONTRACT
    # =====================================

    app.add_handler(
        admin_wallet_handler
    )

    app.add_handler(
        admin_contract_handler
    )

    app.add_handler(
        admin_contract_termination_handler
    )

    # =====================================
    # ADMIN BAN / UNBAN
    # =====================================

    app.add_handler(
        ban_user_handler
    )

    app.add_handler(
        unban_user_handler
    )

    # =====================================
    # ADMIN MESSAGE
    # =====================================

    app.add_handler(
        admin_message_handler
    )

    app.add_handler(
        user_reply_handler
    )

    # =====================================
    # KYC ADMIN
    # =====================================

    app.add_handler(
        approve_kyc_handler
    )

    app.add_handler(
        reject_kyc_handler
    )

    app.add_handler(
        kyc_callback_handler
    )

    app.add_handler(
        admin_kyc_status_handler
    )

    app.add_handler(
        manual_kyc_status_callback_handler
    )

    # =====================================
    # USER CONVERSATION HANDLERS
    # =====================================

    app.add_handler(
        registration_handler
    )

    app.add_handler(
        kyc_handler
    )

    app.add_handler(
        deposit_handler
    )

    app.add_handler(
        submit_tx_handler
    )

    app.add_handler(
        refund_handler
    )

    app.add_handler(
        help_handler
    )

    app.add_handler(
        faq_handler
    )

    app.add_handler(
        terms_handler
    )

    app.add_handler(
        privacy_handler
    )

    app.add_handler(
        withdraw_handler
    )

    app.add_handler(
        change_withdrawal_address_handler
    )

    # =====================================
    # PAGE REGISTRY
    # =====================================

    register_page(
        "main_menu",
        show_main_menu,
    )

    register_page(
        "wallet",
        wallet,
    )

    register_page(
        "fund_wallet",
        fund_wallet,
    )

    register_page(
        "deposit",
        select_btc,
    )

    # =====================================
    # CRYPTO MARKET BROADCAST SCHEDULE
    # =====================================
    #
    # Fixed UTC schedule:
    #
    # 00:00 UTC
    # 03:00 UTC
    # 06:00 UTC
    # 09:00 UTC
    # 12:00 UTC
    # 15:00 UTC
    # 18:00 UTC
    # 21:00 UTC
    #
    # Using run_daily prevents Railway
    # restarts from causing an immediate
    # unexpected broadcast.
    # =====================================

    crypto_broadcast_times = [
        (0, 0),
        (3, 0),
        (6, 0),
        (9, 0),
        (12, 0),
        (15, 0),
        (18, 0),
        (21, 0),
    ]

    for hour, minute in crypto_broadcast_times:

        app.job_queue.run_daily(
            crypto_broadcast_job,
            time=time(
                hour=hour,
                minute=minute,
                tzinfo=timezone.utc,
            ),
            name=f"crypto_market_{hour:02d}{minute:02d}",
        )

    # =====================================
    # START BOT
    # =====================================

    print(
        "✅ NebuMine Pro Bot Started"
    )

    app.run_polling()


# =====================================
# ENTRY POINT
# =====================================

if __name__ == "__main__":
    main()
