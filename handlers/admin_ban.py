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

from keyboards import (
    admin_menu,
)

from database import (
    user_exists,
    get_user,
    is_user_banned,
    ban_user,
    unban_user,
)


# =====================================
# CONVERSATION STATE
# =====================================

USER_ID = 0


# =====================================
# CANCEL KEYBOARD
# =====================================

cancel_keyboard = ReplyKeyboardMarkup(
    [
        ["❌ Cancel"],
    ],
    resize_keyboard=True,
)


# =====================================
# START BAN
# =====================================

async def start_ban_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return ConversationHandler.END

    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    # Clear any previous temporary data
    context.user_data.clear()

    await update.message.reply_text(
        "🚫 *Ban User*\n\n"
        "Enter the Telegram User ID you want to ban.\n\n"
        "Example:\n"
        "`123456789`",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard,
    )

    return USER_ID


# =====================================
# RECEIVE BAN USER ID
# =====================================

async def receive_ban_user_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return ConversationHandler.END

    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    if not update.message:
        return USER_ID

    text = (
        update.message.text.strip()
        if update.message.text
        else ""
    )

    # =====================================
    # CANCEL
    # =====================================

    if text == "❌ Cancel":

        context.user_data.clear()

        await update.message.reply_text(
            "❌ Ban operation cancelled.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    # =====================================
    # VALIDATE USER ID
    # =====================================

    try:

        user_id = int(text)

    except (TypeError, ValueError):

        await update.message.reply_text(
            "❌ Invalid User ID.\n\n"
            "Please enter the numeric "
            "Telegram User ID."
        )

        return USER_ID

    # =====================================
    # PREVENT ADMIN FROM BEING BANNED
    # =====================================

    if user_id == ADMIN_ID:

        await update.message.reply_text(
            "❌ You cannot ban the administrator."
        )

        return USER_ID

    # =====================================
    # USER EXISTS?
    # =====================================

    try:

        exists = user_exists(
            user_id
        )

    except Exception as exc:

        print(
            f"❌ User existence check failed "
            f"for {user_id}: {exc}"
        )

        await update.message.reply_text(
            "❌ Database error while checking "
            "the user. Please try again."
        )

        return USER_ID

    if not exists:

        await update.message.reply_text(
            "❌ User not found.\n\n"
            "Please check the Telegram User ID "
            "and try again."
        )

        return USER_ID

    # =====================================
    # ALREADY BANNED?
    # =====================================

    try:

        already_banned = is_user_banned(
            user_id
        )

    except Exception as exc:

        print(
            f"❌ Ban status check failed "
            f"for {user_id}: {exc}"
        )

        await update.message.reply_text(
            "❌ Database error while checking "
            "the user's ban status."
        )

        return USER_ID

    if already_banned:

        context.user_data.clear()

        await update.message.reply_text(
            "⚠️ This user is already banned.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    # =====================================
    # GET USER
    # =====================================

    try:

        user = get_user(
            user_id
        )

    except Exception as exc:

        print(
            f"❌ Could not retrieve user "
            f"{user_id}: {exc}"
        )

        await update.message.reply_text(
            "❌ Could not retrieve user information."
        )

        return USER_ID

    full_name = (
        user[1]
        if user and len(user) > 1 and user[1]
        else "Unknown User"
    )

    # =====================================
    # SAVE TEMPORARY USER ID
    # =====================================

    context.user_data["ban_user_id"] = user_id

    # =====================================
    # CONFIRMATION BUTTONS
    # =====================================

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🚫 Confirm Ban",
                    callback_data="confirm_ban_user",
                ),
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="cancel_ban_user",
                ),
            ]
        ]
    )

    await update.message.reply_text(
        "⚠️ *Confirm User Ban*\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 User: {full_name}\n"
        f"🆔 User ID: `{user_id}`\n\n"
        "This will immediately restrict the "
        "user from using the bot.\n\n"
        "━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

    return USER_ID


# =====================================
# BAN CALLBACK
# =====================================

async def ban_user_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await query.answer()

    # =====================================
    # ADMIN CHECK
    # =====================================

    if query.from_user.id != ADMIN_ID:

        return ConversationHandler.END

    # =====================================
    # GET STORED USER ID
    # =====================================

    user_id = context.user_data.get(
        "ban_user_id"
    )

    if not user_id:

        await query.edit_message_text(
            "❌ Ban session expired.\n\n"
            "Please start the Ban User process again."
        )

        context.user_data.clear()

        return ConversationHandler.END

    # =====================================
    # CANCEL
    # =====================================

    if query.data == "cancel_ban_user":

        await query.edit_message_text(
            "❌ User ban cancelled."
        )

        context.user_data.clear()

        await query.message.reply_text(
            "🛠 Admin Dashboard",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    # =====================================
    # UNKNOWN CALLBACK
    # =====================================

    if query.data != "confirm_ban_user":

        return USER_ID

    # =====================================
    # PROTECT ADMIN
    # =====================================

    if user_id == ADMIN_ID:

        await query.edit_message_text(
            "❌ The administrator cannot be banned."
        )

        context.user_data.clear()

        return ConversationHandler.END

    # =====================================
    # CHECK CURRENT STATUS
    # =====================================

    try:

        already_banned = is_user_banned(
            user_id
        )

    except Exception as exc:

        print(
            f"❌ Ban status check failed "
            f"for {user_id}: {exc}"
        )

        await query.edit_message_text(
            "❌ Database error while checking "
            "the user's ban status."
        )

        context.user_data.clear()

        return ConversationHandler.END

    if already_banned:

        await query.edit_message_text(
            "⚠️ This user is already banned."
        )

        context.user_data.clear()

        return ConversationHandler.END

    # =====================================
    # BAN USER
    # =====================================

    try:

        success = ban_user(
            user_id
        )

    except Exception as exc:

        print(
            f"❌ Failed to ban user "
            f"{user_id}: {exc}"
        )

        success = False

    if not success:

        await query.edit_message_text(
            "❌ Failed to ban the user.\n\n"
            "No ban was confirmed."
        )

        context.user_data.clear()

        return ConversationHandler.END

    # =====================================
    # ADMIN CONFIRMATION
    # =====================================

    await query.edit_message_text(
        "🚫 *User Banned Successfully*\n\n"
        f"🆔 User ID: `{user_id}`\n\n"
        "The global ban protection is now active.",
        parse_mode="Markdown",
    )

    # =====================================
    # NOTIFY USER
    # =====================================

    try:

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🚫 *Account Restricted*\n\n"
                "Your access to this bot has been "
                "restricted by administration.\n\n"
                "You cannot use the bot while "
                "your account is banned.\n\n"
                "Please contact support if you "
                "believe this was done in error."
            ),
            parse_mode="Markdown",
        )

    except Exception as exc:

        print(
            f"⚠️ Could not notify banned "
            f"user {user_id}: {exc}"
        )

    # =====================================
    # RETURN ADMIN TO MENU
    # =====================================

    await query.message.reply_text(
        "🛠 Admin Dashboard",
        reply_markup=admin_menu,
    )

    context.user_data.clear()

    return ConversationHandler.END


# =====================================
# START UNBAN
# =====================================

async def start_unban_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return ConversationHandler.END

    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    context.user_data.clear()

    await update.message.reply_text(
        "🔓 *Unban User*\n\n"
        "Enter the Telegram User ID you want to unban.\n\n"
        "Example:\n"
        "`123456789`",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard,
    )

    return USER_ID


# =====================================
# RECEIVE UNBAN USER ID
# =====================================

async def receive_unban_user_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return ConversationHandler.END

    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    if not update.message:
        return USER_ID

    text = (
        update.message.text.strip()
        if update.message.text
        else ""
    )

    # =====================================
    # CANCEL
    # =====================================

    if text == "❌ Cancel":

        context.user_data.clear()

        await update.message.reply_text(
            "❌ Unban operation cancelled.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    # =====================================
    # VALIDATE USER ID
    # =====================================

    try:

        user_id = int(text)

    except (TypeError, ValueError):

        await update.message.reply_text(
            "❌ Invalid User ID.\n\n"
            "Please enter the numeric "
            "Telegram User ID."
        )

        return USER_ID

    # =====================================
    # ADMIN CHECK
    # =====================================

    if user_id == ADMIN_ID:

        await update.message.reply_text(
            "ℹ️ The administrator is not banned."
        )

        return USER_ID

    # =====================================
    # USER EXISTS?
    # =====================================

    try:

        exists = user_exists(
            user_id
        )

    except Exception as exc:

        print(
            f"❌ User existence check failed "
            f"for {user_id}: {exc}"
        )

        await update.message.reply_text(
            "❌ Database error while checking "
            "the user."
        )

        return USER_ID

    if not exists:

        await update.message.reply_text(
            "❌ User not found.\n\n"
            "Please check the Telegram User ID "
            "and try again."
        )

        return USER_ID

    # =====================================
    # CHECK BAN STATUS
    # =====================================

    try:

        currently_banned = is_user_banned(
            user_id
        )

    except Exception as exc:

        print(
            f"❌ Ban status check failed "
            f"for {user_id}: {exc}"
        )

        await update.message.reply_text(
            "❌ Database error while checking "
            "the user's ban status."
        )

        return USER_ID

    if not currently_banned:

        context.user_data.clear()

        await update.message.reply_text(
            "ℹ️ This user is not currently banned.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    # =====================================
    # GET USER
    # =====================================

    try:

        user = get_user(
            user_id
        )

    except Exception as exc:

        print(
            f"❌ Could not retrieve user "
            f"{user_id}: {exc}"
        )

        await update.message.reply_text(
            "❌ Could not retrieve user information."
        )

        return USER_ID

    full_name = (
        user[1]
        if user and len(user) > 1 and user[1]
        else "Unknown User"
    )

    # =====================================
    # SAVE TEMPORARY USER ID
    # =====================================

    context.user_data["unban_user_id"] = user_id

    # =====================================
    # CONFIRMATION BUTTONS
    # =====================================

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔓 Confirm Unban",
                    callback_data="confirm_unban_user",
                ),
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="cancel_unban_user",
                ),
            ]
        ]
    )

    await update.message.reply_text(
        "⚠️ *Confirm User Unban*\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 User: {full_name}\n"
        f"🆔 User ID: `{user_id}`\n\n"
        "The user will regain access to the bot "
        "after confirmation.\n\n"
        "━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

    return USER_ID


# =====================================
# UNBAN CALLBACK
# =====================================

async def unban_user_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await query.answer()

    # =====================================
    # ADMIN CHECK
    # =====================================

    if query.from_user.id != ADMIN_ID:

        return ConversationHandler.END

    # =====================================
    # GET STORED USER ID
    # =====================================

    user_id = context.user_data.get(
        "unban_user_id"
    )

    if not user_id:

        await query.edit_message_text(
            "❌ Unban session expired.\n\n"
            "Please start the Unban User process again."
        )

        context.user_data.clear()

        return ConversationHandler.END

    # =====================================
    # CANCEL
    # =====================================

    if query.data == "cancel_unban_user":

        await query.edit_message_text(
            "❌ User unban cancelled."
        )

        context.user_data.clear()

        await query.message.reply_text(
            "🛠 Admin Dashboard",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    # =====================================
    # UNKNOWN CALLBACK
    # =====================================

    if query.data != "confirm_unban_user":

        return USER_ID

    # =====================================
    # CHECK CURRENT STATUS
    # =====================================

    try:

        currently_banned = is_user_banned(
            user_id
        )

    except Exception as exc:

        print(
            f"❌ Ban status check failed "
            f"for {user_id}: {exc}"
        )

        await query.edit_message_text(
            "❌ Database error while checking "
            "the user's ban status."
        )

        context.user_data.clear()

        return ConversationHandler.END

    if not currently_banned:

        await query.edit_message_text(
            "ℹ️ This user is no longer banned."
        )

        context.user_data.clear()

        return ConversationHandler.END

    # =====================================
    # UNBAN USER
    # =====================================

    try:

        success = unban_user(
            user_id
        )

    except Exception as exc:

        print(
            f"❌ Failed to unban user "
            f"{user_id}: {exc}"
        )

        success = False

    if not success:

        await query.edit_message_text(
            "❌ Failed to unban the user.\n\n"
            "The user remains banned."
        )

        context.user_data.clear()

        return ConversationHandler.END

    # =====================================
    # ADMIN CONFIRMATION
    # =====================================

    await query.edit_message_text(
        "🔓 *User Unbanned Successfully*\n\n"
        f"🆔 User ID: `{user_id}`\n\n"
        "The user can use the bot again.",
        parse_mode="Markdown",
    )

    # =====================================
    # NOTIFY USER
    # =====================================

    try:

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🔓 *Account Access Restored*\n\n"
                "Your access to the bot has been "
                "restored by administration.\n\n"
                "You can now use the bot normally."
            ),
            parse_mode="Markdown",
        )

    except Exception as exc:

        print(
            f"⚠️ Could not notify unbanned "
            f"user {user_id}: {exc}"
        )

    # =====================================
    # RETURN ADMIN TO MENU
    # =====================================

    await query.message.reply_text(
        "🛠 Admin Dashboard",
        reply_markup=admin_menu,
    )

    context.user_data.clear()

    return ConversationHandler.END


# =====================================
# BAN CONVERSATION
# =====================================

ban_user_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex(
                r"^🚫 Ban User$"
            ),
            start_ban_user,
        ),
    ],
    states={
        USER_ID: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_ban_user_id,
            ),
            CallbackQueryHandler(
                ban_user_callback,
                pattern=r"^(confirm_ban_user|cancel_ban_user)$",
            ),
        ],
    },
    fallbacks=[
        MessageHandler(
            filters.Regex(
                r"^❌ Cancel$"
            ),
            receive_ban_user_id,
        ),
    ],
)


# =====================================
# UNBAN CONVERSATION
# =====================================

unban_user_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex(
                r"^🔓 Unban User$"
            ),
            start_unban_user,
        ),
    ],
    states={
        USER_ID: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_unban_user_id,
            ),
            CallbackQueryHandler(
                unban_user_callback,
                pattern=r"^(confirm_unban_user|cancel_unban_user)$",
            ),
        ],
    },
    fallbacks=[
        MessageHandler(
            filters.Regex(
                r"^❌ Cancel$"
            ),
            receive_unban_user_id,
        ),
    ],
)
