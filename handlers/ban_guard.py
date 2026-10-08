from telegram import Update
from telegram.ext import (
    ContextTypes,
    ApplicationHandlerStop,
)

from config import ADMIN_ID

from database import (
    is_user_banned,
)


# =====================================
# GLOBAL BAN CHECK
# =====================================

async def global_ban_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    # No Telegram user attached to update
    if not user:
        return

    user_id = user.id

    # =====================================
    # ADMIN EXEMPTION
    # =====================================

    if user_id == ADMIN_ID:
        return

    # =====================================
    # CHECK BAN STATUS
    # =====================================

    try:

        banned = is_user_banned(
            user_id
        )

    except Exception as exc:

        print(
            f"⚠️ Global ban check failed "
            f"for user {user_id}: {exc}"
        )

        # Fail open.
        #
        # A temporary Supabase/database error
        # should not accidentally block every
        # user from the bot.
        return

    if not banned:
        return

    # =====================================
    # BANNED CALLBACK QUERY
    # =====================================

    if update.callback_query:

        try:

            await update.callback_query.answer(
                "🚫 Your account is banned.",
                show_alert=True,
            )

        except Exception as exc:

            print(
                f"⚠️ Could not answer banned "
                f"callback for {user_id}: {exc}"
            )

        # Stop this update from reaching
        # any other handler.
        raise ApplicationHandlerStop

    # =====================================
    # BANNED MESSAGE
    # =====================================

    if update.message:

        try:

            await update.message.reply_text(
                "🚫 *Account Banned*\n\n"
                "Your account has been restricted "
                "by administration.\n\n"
                "You cannot use the bot while "
                "your account is banned.\n\n"
                "Please contact support if you "
                "believe this was done in error.",
                parse_mode="Markdown",
            )

        except Exception as exc:

            print(
                f"⚠️ Could not notify banned "
                f"user {user_id}: {exc}"
            )

        # Stop this update from reaching
        # commands, menus, or active
        # ConversationHandlers.
        raise ApplicationHandlerStop

    # =====================================
    # ANY OTHER UPDATE TYPE
    # =====================================

    raise ApplicationHandlerStop
