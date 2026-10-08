from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
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
    update_kyc_status,
)

from keyboards import admin_menu


# ==========================================
# CONVERSATION STATE
# ==========================================

USER_ID = 0


# ==========================================
# TEMPORARY CANCEL KEYBOARD
# ==========================================

cancel_keyboard = ReplyKeyboardMarkup(
    [
        ["❌ Cancel"],
    ],
    resize_keyboard=True,
)


# ==========================================
# START CHANGE KYC STATUS
# ==========================================

async def start_change_kyc_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    context.user_data.clear()

    await update.message.reply_text(
        "🪪 *Change KYC Status*\n\n"
        "Enter the Telegram User ID:",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard,
    )

    return USER_ID


# ==========================================
# RECEIVE USER ID
# ==========================================

async def receive_kyc_user_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    text = (update.message.text or "").strip()

    # ==========================================
    # CANCEL
    # ==========================================

    if text == "❌ Cancel":

        context.user_data.clear()

        await update.message.reply_text(
            "❌ KYC status change cancelled.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    # ==========================================
    # VALIDATE USER ID
    # ==========================================

    try:

        user_id = int(text)

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid User ID.\n\n"
            "Please enter the numeric Telegram User ID.",
            reply_markup=cancel_keyboard,
        )

        return USER_ID

    # ==========================================
    # CHECK USER EXISTS
    # ==========================================

    if not user_exists(user_id):

        await update.message.reply_text(
            "❌ User not found.\n\n"
            "Please check the Telegram User ID and try again.",
            reply_markup=cancel_keyboard,
        )

        return USER_ID

    # ==========================================
    # GET USER
    # ==========================================

    user = get_user(user_id)

    if not user:

        await update.message.reply_text(
            "❌ Unable to retrieve this user.",
            reply_markup=cancel_keyboard,
        )

        return USER_ID

    # ==========================================
    # USER DATA
    # ==========================================

    # _user_tuple() places:
    #
    # index 0 = user_id
    # index 1 = full_name
    # index 6 = kyc_status

    full_name = user[1] or "User"
    current_status = user[6] or "Pending"

    context.user_data["kyc_user_id"] = user_id
    context.user_data["kyc_user_name"] = full_name

    # ==========================================
    # STATUS BUTTONS
    # ==========================================

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approved",
                    callback_data=f"manual_kyc:Approved:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Rejected",
                    callback_data=f"manual_kyc:Rejected:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⏳ Pending",
                    callback_data=f"manual_kyc:Pending:{user_id}",
                )
            ],
        ]
    )

    await update.message.reply_text(
        "🪪 *KYC Status Management*\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 User: *{full_name}*\n"
        f"🆔 User ID: `{user_id}`\n\n"
        f"Current Status: *{current_status}*\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Select the new KYC status:",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

    # ==========================================
    # REMOVE TEMPORARY CANCEL KEYBOARD
    # ==========================================

    await update.message.reply_text(
        "Select a KYC status above.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


# ==========================================
# PROCESS STATUS CHANGE
# ==========================================

async def process_manual_kyc_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    # ==========================================
    # ADMIN ONLY
    # ==========================================

    if query.from_user.id != ADMIN_ID:
        return

    # ==========================================
    # CANCEL CALLBACK
    # ==========================================
    #
    # Kept for compatibility with any old
    # inline buttons/messages that may still
    # contain manual_kyc_cancel.
    #
    # New status menu does NOT display this
    # button anymore.
    # ==========================================

    if query.data == "manual_kyc_cancel":

        await query.edit_message_text(
            "❌ KYC status change cancelled."
        )

        context.user_data.clear()

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="🛠 *Admin Panel*",
            parse_mode="Markdown",
            reply_markup=admin_menu,
        )

        return

    # ==========================================
    # PARSE CALLBACK
    # ==========================================

    try:

        _, status, user_id_text = query.data.split(":")

        user_id = int(user_id_text)

    except (ValueError, AttributeError):

        await query.edit_message_text(
            "❌ Invalid KYC status request."
        )

        context.user_data.clear()

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="🛠 *Admin Panel*",
            parse_mode="Markdown",
            reply_markup=admin_menu,
        )

        return

    # ==========================================
    # VALID STATUS
    # ==========================================

    if status not in (
        "Approved",
        "Rejected",
        "Pending",
    ):

        await query.edit_message_text(
            "❌ Invalid KYC status."
        )

        context.user_data.clear()

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="🛠 *Admin Panel*",
            parse_mode="Markdown",
            reply_markup=admin_menu,
        )

        return

    # ==========================================
    # GET USER
    # ==========================================

    user = get_user(user_id)

    if not user:

        await query.edit_message_text(
            "❌ User no longer exists."
        )

        context.user_data.clear()

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="🛠 *Admin Panel*",
            parse_mode="Markdown",
            reply_markup=admin_menu,
        )

        return

    # ==========================================
    # USER DATA
    # ==========================================

    full_name = user[1] or "User"
    old_status = user[6] or "Pending"

    # ==========================================
    # UPDATE SUPABASE
    # ==========================================

    result = update_kyc_status(
        user_id,
        status,
    )

    if not result:

        await query.edit_message_text(
            "❌ Failed to update the KYC status."
        )

        context.user_data.clear()

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="🛠 *Admin Panel*",
            parse_mode="Markdown",
            reply_markup=admin_menu,
        )

        return

    # ==========================================
    # NOTIFY USER
    # ==========================================

    try:

        if status == "Approved":

            user_message = (
                "🎉 *KYC Approved!*\n\n"
                "Your KYC verification has been approved.\n\n"
                "You now have full access to "
                "NebuMine Pro."
            )

        elif status == "Rejected":

            user_message = (
                "❌ *KYC Rejected*\n\n"
                "Unfortunately, your KYC verification "
                "could not be approved.\n\n"
                "Please submit a clearer government-issued "
                "ID and a clear selfie holding the ID."
            )

        else:

            user_message = (
                "⏳ *KYC Status Updated*\n\n"
                "Your KYC status has been changed to "
                "*Pending*.\n\n"
                "Please wait while your verification "
                "is being reviewed."
            )

        await context.bot.send_message(
            chat_id=user_id,
            text=user_message,
            parse_mode="Markdown",
        )

        user_notified = True

    except Exception as e:

        print(
            f"Failed to notify user {user_id} "
            f"about KYC status change: {e}"
        )

        user_notified = False

    # ==========================================
    # NOTIFICATION RESULT
    # ==========================================

    notification_text = (
        "📨 User notified."
        if user_notified
        else "⚠️ Status updated, but user notification failed."
    )

    # ==========================================
    # ADMIN CONFIRMATION
    # ==========================================

    await query.edit_message_text(
        "✅ *KYC Status Updated*\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 User: *{full_name}*\n"
        f"🆔 User ID: `{user_id}`\n\n"
        f"Previous Status: *{old_status}*\n"
        f"New Status: *{status}*\n\n"
        f"{notification_text}",
        parse_mode="Markdown",
    )

    # ==========================================
    # CLEAR TEMPORARY DATA
    # ==========================================

    context.user_data.clear()

    # ==========================================
    # RESTORE ADMIN MENU
    # ==========================================
    #
    # This replaces the temporary Cancel
    # keyboard with the normal Admin Menu.
    # ==========================================

    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="🛠 *Admin Panel*",
        parse_mode="Markdown",
        reply_markup=admin_menu,
    )


# ==========================================
# CANCEL CONVERSATION
# ==========================================

async def cancel_change_kyc_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    context.user_data.clear()

    await update.message.reply_text(
        "❌ KYC status change cancelled.",
        reply_markup=admin_menu,
    )

    return ConversationHandler.END


# ==========================================
# ADMIN KYC STATUS HANDLER
# ==========================================

admin_kyc_status_handler = ConversationHandler(

    entry_points=[
        MessageHandler(
            filters.Regex("^🪪 Change KYC Status$"),
            start_change_kyc_status,
        )
    ],

    states={

        USER_ID: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_kyc_user_id,
            )
        ],

    },

    fallbacks=[
        MessageHandler(
            filters.Regex("^❌ Cancel$"),
            cancel_change_kyc_status,
        )
    ],

)


# ==========================================
# INLINE STATUS CALLBACK HANDLER
# ==========================================

manual_kyc_status_callback_handler = CallbackQueryHandler(
    process_manual_kyc_status,
    pattern=r"^manual_kyc:(Approved|Rejected|Pending):\d+$|^manual_kyc_cancel$",
)
