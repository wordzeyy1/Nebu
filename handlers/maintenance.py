
import os

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Railway variable example: ADMIN_IDS=123456789,987654321
ADMIN_IDS = {
    int(user_id.strip())
    for user_id in os.getenv("ADMIN_IDS", "").split(",")
    if user_id.strip().isdigit()
}

# This flag lasts until the bot restarts.
maintenance_enabled = False

MAINTENANCE_NOTICE = (
    "🛠️ <b>Maintenance in Progress</b>\n\n"
    "The bot is temporarily unavailable while we perform maintenance.\n"
    "Your mining operations continue running in the background.\n\n"
    "Please try again later. Thank you for your patience."
)


def is_admin(user_id: int | None) -> bool:
    return user_id is not None and user_id in ADMIN_IDS


async def maintenance_on(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    global maintenance_enabled

    user = update.effective_user

    if not is_admin(user.id if user else None):
        if update.effective_message:
            await update.effective_message.reply_text(
                "⛔ You are not authorized to use this command.",
                reply_markup=ReplyKeyboardRemove(),
            )
        raise ApplicationHandlerStop

    maintenance_enabled = True

    if update.effective_message:
        await update.effective_message.reply_text(
            "🛠️ Maintenance mode is now ON.\n"
            "Normal users are blocked. Background mining jobs will continue."
        )

    raise ApplicationHandlerStop


async def maintenance_off(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    global maintenance_enabled

    user = update.effective_user

    if not is_admin(user.id if user else None):
        if update.effective_message:
            await update.effective_message.reply_text(
                "⛔ You are not authorized to use this command.",
                reply_markup=ReplyKeyboardRemove(),
            )
        raise ApplicationHandlerStop

    maintenance_enabled = False

    if update.effective_message:
        await update.effective_message.reply_text(
            "✅ Maintenance mode is now OFF. Normal bot access is restored."
        )

    raise ApplicationHandlerStop


async def maintenance_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user = update.effective_user

    if not is_admin(user.id if user else None):
        if update.effective_message:
            await update.effective_message.reply_text(
                "⛔ You are not authorized to use this command."
            )
        raise ApplicationHandlerStop

    status = "ON 🛠️" if maintenance_enabled else "OFF ✅"

    if update.effective_message:
        await update.effective_message.reply_text(
            f"Maintenance mode: {status}"
        )

    raise ApplicationHandlerStop


async def block_user_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Block ordinary user messages and commands during maintenance."""
    if not maintenance_enabled:
        return

    user = update.effective_user

    # Admins can continue using the bot normally.
    if is_admin(user.id if user else None):
        return

    message = update.effective_message
    if message:
        await message.reply_text(
            MAINTENANCE_NOTICE,
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )

    # Stop this update from reaching normal bot handlers.
    raise ApplicationHandlerStop


async def block_stale_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Block old inline buttons while maintenance is active."""
    if not maintenance_enabled:
        return

    query = update.callback_query
    if not query:
        return

    user = update.effective_user

    # Admins retain normal inline-button access.
    if is_admin(user.id if user else None):
        return

    # Stop the Telegram loading spinner.
    await query.answer()

    # Remove the old inline keyboard where possible.
    if query.message:
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception as exc:
            # The message may be too old, inaccessible, or already edited.
            print(f"Could not remove stale inline keyboard: {exc}")

        await query.message.reply_text(
            MAINTENANCE_NOTICE,
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        # Handles callbacks from inline-mode messages.
        await query.answer(
            "Maintenance is in progress. Please try again later.",
            show_alert=True,
        )

    raise ApplicationHandlerStop


def register_maintenance_handlers(application) -> None:
    """Register these handlers before ordinary user handlers by group."""

    # Admin maintenance commands run before the global maintenance gate.
    application.add_handler(
        CommandHandler("maintenance_on", maintenance_on),
        group=-2,
    )
    application.add_handler(
        CommandHandler("maintenance_off", maintenance_off),
        group=-2,
    )
    application.add_handler(
        CommandHandler("maintenance_status", maintenance_status),
        group=-2,
    )

    # Block normal messages and stale callback buttons before business handlers.
    application.add_handler(
        MessageHandler(filters.ALL, block_user_message),
        group=-1,
    )
    application.add_handler(
        CallbackQueryHandler(block_stale_callback),
        group=-1,
)
      
