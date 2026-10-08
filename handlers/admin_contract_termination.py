from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import ADMIN_ID

from database import (
    user_exists,
    get_user,
    get_active_contracts,
    get_mining_contract,
    terminate_mining_contract,
    add_wallet_balance,
    record_wallet_transaction,
)

from keyboards import admin_menu


# ==========================================
# STATES
# ==========================================

USER_ID, SELECT_CONTRACT = range(2)


# ==========================================
# CANCEL KEYBOARD
# ==========================================

cancel_keyboard = ReplyKeyboardMarkup(
    [
        ["❌ Cancel"],
    ],
    resize_keyboard=True,
)


# ==========================================
# START TERMINATION
# ==========================================

async def start_terminate_contract(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    context.user_data.pop("termination_user_id", None)
    context.user_data.pop("termination_contract_id", None)

    await update.message.reply_text(
        "⛏ *Terminate Mining Contract*\n\n"
        "Enter the Telegram User ID of the user "
        "whose mining contract you want to terminate.",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard,
    )

    return USER_ID


# ==========================================
# RECEIVE USER ID
# ==========================================

async def receive_termination_user_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    text = update.message.text.strip()

    if text == "❌ Cancel":

        context.user_data.clear()

        await update.message.reply_text(
            "❌ Contract termination cancelled.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    try:
        user_id = int(text)

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid User ID.\n\n"
            "Please enter the numeric Telegram User ID."
        )

        return USER_ID

    if not user_exists(user_id):

        await update.message.reply_text(
            "❌ User not found.\n\n"
            "Please check the Telegram User ID and try again."
        )

        return USER_ID

    contracts = get_active_contracts(user_id)

    if not contracts:

        await update.message.reply_text(
            "❌ This user has no active mining contracts.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    context.user_data["termination_user_id"] = user_id

    user = get_user(user_id)

    if user:
        full_name = user[1] or "User"
    else:
        full_name = "User"

    buttons = []

    for contract in contracts:

        contract_id = contract[0]
        hash_power = float(contract[2] or 0)
        purchase_price = float(contract[3] or 0)

        buttons.append(
            [
                InlineKeyboardButton(
                    (
                        f"⛏ #{contract_id} | "
                        f"{hash_power:.2f} TH/s | "
                        f"${purchase_price:,.2f}"
                    ),
                    callback_data=f"terminate_contract:{contract_id}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="terminate_contract_cancel",
            )
        ]
    )

    await update.message.reply_text(
        "⛏ *Active Mining Contracts*\n\n"
        f"👤 User: *{full_name}*\n"
        f"🆔 User ID: `{user_id}`\n\n"
        "Select the contract you want to terminate.\n\n"
        "The original contract purchase amount will "
        "be refunded to the user's wallet.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

    return SELECT_CONTRACT


# ==========================================
# SELECT CONTRACT
# ==========================================

async def select_termination_contract(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return ConversationHandler.END

    if query.data == "terminate_contract_cancel":

        context.user_data.clear()

        await query.edit_message_text(
            "❌ Contract termination cancelled."
        )

        await query.message.reply_text(
            "🛠 Admin Dashboard",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    try:
        _, contract_id_text = query.data.split(":", 1)
        contract_id = int(contract_id_text)

    except (ValueError, TypeError):

        await query.edit_message_text(
            "❌ Invalid contract."
        )

        context.user_data.clear()

        return ConversationHandler.END

    contract = get_mining_contract(contract_id)

    if not contract:

        await query.edit_message_text(
            "❌ Contract not found."
        )

        context.user_data.clear()

        return ConversationHandler.END

    contract_user_id = contract[1]
    hash_power = float(contract[2] or 0)
    purchase_price = float(contract[3] or 0)
    daily_income = float(contract[4] or 0)
    purchase_date = contract[5]
    status = contract[7]

    # ==========================================
    # SECURITY CHECK
    # ==========================================

    selected_user_id = context.user_data.get(
        "termination_user_id"
    )

    if selected_user_id != contract_user_id:

        await query.edit_message_text(
            "❌ Security check failed.\n\n"
            "The selected contract does not belong "
            "to the selected user."
        )

        context.user_data.clear()

        return ConversationHandler.END

    # ==========================================
    # ACTIVE CHECK
    # ==========================================

    if status != "Active":

        await query.edit_message_text(
            "❌ This contract is no longer active.\n\n"
            "It cannot be terminated or refunded again."
        )

        context.user_data.clear()

        return ConversationHandler.END

    context.user_data["termination_contract_id"] = contract_id

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Confirm Termination",
                    callback_data="confirm_contract_termination",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="cancel_contract_termination",
                )
            ],
        ]
    )

    await query.edit_message_text(
        "⚠️ *Confirm Contract Termination*\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"⛏ Contract ID: `{contract_id}`\n"
        f"⚡ Hash Power: `{hash_power:.2f} TH/s`\n"
        f"💰 Purchase Amount: `${purchase_price:,.2f}`\n"
        f"📈 Daily Income: `${daily_income:,.2f}`\n"
        f"📅 Purchase Date: `{purchase_date}`\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"💵 *Refund: ${purchase_price:,.2f}*\n\n"
        "The contract will be changed from "
        "*Active* to *Terminated*.\n\n"
        "The original purchase amount will be "
        "credited to the user's wallet.\n\n"
        "⚠️ This action should only be performed "
        "when the contract is intended to be terminated.",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

    return SELECT_CONTRACT


# ==========================================
# CONFIRM / CANCEL TERMINATION
# ==========================================

async def contract_termination_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return ConversationHandler.END

    if query.data == "cancel_contract_termination":

        context.user_data.clear()

        await query.edit_message_text(
            "❌ Contract termination cancelled."
        )

        await query.message.reply_text(
            "🛠 Admin Dashboard",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    contract_id = context.user_data.get(
        "termination_contract_id"
    )

    if not contract_id:

        await query.edit_message_text(
            "❌ Termination session expired."
        )

        context.user_data.clear()

        return ConversationHandler.END

    # ==========================================
    # RE-CHECK CONTRACT
    # ==========================================

    contract = get_mining_contract(contract_id)

    if not contract:

        await query.edit_message_text(
            "❌ Contract no longer exists."
        )

        context.user_data.clear()

        return ConversationHandler.END

    user_id = contract[1]
    hash_power = float(contract[2] or 0)
    purchase_price = float(contract[3] or 0)
    status = contract[7]

    # ==========================================
    # DUPLICATE REFUND PROTECTION
    # ==========================================

    if status != "Active":

        await query.edit_message_text(
            "❌ This contract has already been "
            "terminated or is no longer active.\n\n"
            "No additional refund was issued."
        )

        context.user_data.clear()

        return ConversationHandler.END

    # ==========================================
    # TERMINATE CONTRACT
    # ==========================================

    terminated_contract = terminate_mining_contract(
        contract_id
    )

    if not terminated_contract:

        await query.edit_message_text(
            "❌ The contract could not be terminated.\n\n"
            "It may have already been terminated."
        )

        context.user_data.clear()

        return ConversationHandler.END

    # ==========================================
    # REFUND PURCHASE AMOUNT
    # ==========================================

    refund_amount = purchase_price

    refund_success = add_wallet_balance(
        user_id,
        refund_amount,
    )

    if not refund_success:

        # The contract has already been changed to
        # Terminated. Do not issue another refund
        # automatically.
        await query.edit_message_text(
            "⚠️ Contract terminated, but the wallet "
            "refund could not be credited automatically.\n\n"
            f"Contract: #{contract_id}\n"
            f"Refund required: ${refund_amount:,.2f}\n\n"
            "Please use Credit Wallet to manually "
            "credit the user."
        )

        context.user_data.clear()

        return ConversationHandler.END

    # ==========================================
    # RECORD TRANSACTION
    # ==========================================

    record_wallet_transaction(
        user_id=user_id,
        transaction_type="Mining Contract Refund",
        amount=refund_amount,
        reason=(
            f"Admin terminated mining contract "
            f"#{contract_id}"
        ),
    )

    # ==========================================
    # GET USER NAME
    # ==========================================

    user = get_user(user_id)

    if user:
        full_name = user[1] or "User"
    else:
        full_name = "User"

    # ==========================================
    # NOTIFY USER
    # ==========================================

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "⚠️ *Mining Contract Terminated*\n\n"
            "Your mining contract has been terminated "
            "by the administration.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"⛏ Contract ID: *#{contract_id}*\n"
            f"⚡ Hash Power: *{hash_power:.2f} TH/s*\n"
            f"💰 Original Purchase: "
            f"*${purchase_price:,.2f}*\n"
            f"💵 Refund Credited: "
            f"*${refund_amount:,.2f}*\n"
            "🔴 Status: *Terminated*\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "The refund has been credited to your "
            "wallet balance."
        ),
        parse_mode="Markdown",
    )

    # ==========================================
    # ADMIN CONFIRMATION
    # ==========================================

    await query.edit_message_text(
        "✅ *Mining Contract Terminated*\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 User: {full_name}\n"
        f"🆔 User ID: `{user_id}`\n"
        f"⛏ Contract ID: `{contract_id}`\n"
        f"⚡ Hash Power: `{hash_power:.2f} TH/s`\n"
        f"💰 Original Purchase: "
        f"`${purchase_price:,.2f}`\n"
        f"💵 Refund Credited: "
        f"`${refund_amount:,.2f}`\n"
        "🔴 Status: `Terminated`\n\n"
        "The refund was added to the user's wallet.",
        parse_mode="Markdown",
    )

    await query.message.reply_text(
        "🛠 Admin Dashboard",
        reply_markup=admin_menu,
    )

    context.user_data.clear()

    return ConversationHandler.END


# ==========================================
# HANDLER
# ==========================================

admin_contract_termination_handler = ConversationHandler(

    entry_points=[
        MessageHandler(
            filters.Regex(
                "^⛏ Terminate Mining Contract$"
            ),
            start_terminate_contract,
        )
    ],

    states={

        USER_ID: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_termination_user_id,
            )
        ],

        SELECT_CONTRACT: [
            CallbackQueryHandler(
                select_termination_contract,
                pattern=r"^terminate_contract:\d+$|^terminate_contract_cancel$",
            ),
            CallbackQueryHandler(
                contract_termination_confirmation,
                pattern=r"^confirm_contract_termination$|^cancel_contract_termination$",
            ),
        ],

    },

    fallbacks=[
        MessageHandler(
            filters.Regex("^❌ Cancel$"),
            start_terminate_contract,
        )
    ],
)
