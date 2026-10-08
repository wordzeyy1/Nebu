from telegram import Update, ReplyKeyboardMarkup
from telegram.helpers import escape
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import ADMIN_ID
from database import user_exists, get_user
from keyboards import admin_menu


USER_ID, MESSAGE = range(2)


cancel_keyboard = ReplyKeyboardMarkup(
    [
        ["❌ Cancel"],
    ],
    resize_keyboard=True,
)


# ==================================================
# TEMPORARY USER MESSAGE MAPPING
# ==================================================
#
# Maps the bot's outgoing message_id to the user_id.
#
# Example:
#
# {
#     1250: 123456789
# }
#
# This allows us to know which user a reply belongs to.
#
# NOTE:
# This mapping is stored in memory.
# If Railway restarts, old mappings are cleared.
# New messages will work normally.
# ==================================================

admin_message_map = {}


# ==================================================
# COPYABLE MESSAGE FORMATTER
# ==================================================
#
# Anything written inside [ ] by the admin becomes
# a Telegram copy-friendly <code>...</code> section.
#
# Example:
#
# Wallet Address:
# [0x123456789]
#
# Transaction Hash:
# [abc123456]
#
# Only the content inside [ ] becomes copyable.
# ==================================================

def format_copyable_message(message: str) -> str:

    import re

    parts = []
    last_end = 0

    for match in re.finditer(
        r"\[([^\]]+)\]",
        message,
    ):

        # ------------------------------------------
        # Normal text before the copyable section
        # ------------------------------------------

        normal_text = message[
            last_end:match.start()
        ]

        if normal_text:
            parts.append(
                escape(normal_text)
            )

        # ------------------------------------------
        # Copyable section
        # ------------------------------------------

        copyable_text = match.group(1)

        parts.append(
            f"<code>{escape(copyable_text)}</code>"
        )

        last_end = match.end()

    # ------------------------------------------
    # Remaining normal text
    # ------------------------------------------

    remaining = message[last_end:]

    if remaining:
        parts.append(
            escape(remaining)
        )

    return "".join(parts)


# ==================================================
# REPLY INSTRUCTIONS
# ==================================================

REPLY_INSTRUCTIONS = (
    "\n\n"
    "💬 <b>How to Reply</b>\n\n"
    "To respond to this message:\n\n"
    "1️⃣ Tap and hold this message (or tap the message).\n"
    "2️⃣ Select <b>↩️ Reply</b>.\n"
    "3️⃣ Type your message.\n"
    "4️⃣ Tap <b>Send</b>.\n\n"
    "Your reply will be delivered directly to the admin/support team."
)


# ==================================================
# START MESSAGE USER
# ==================================================

async def start_message_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    context.user_data.clear()

    await update.message.reply_text(
        "📨 *Message User*\n\n"
        "Enter the Telegram User ID of the person you want to message.",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard,
    )

    return USER_ID


# ==================================================
# RECEIVE USER ID
# ==================================================

async def receive_message_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.message.text == "❌ Cancel":

        context.user_data.clear()

        await update.message.reply_text(
            "❌ Cancelled.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    try:

        user_id = int(
            update.message.text.strip()
        )

    except (ValueError, AttributeError):

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

    context.user_data["message_user_id"] = user_id

    user = get_user(user_id)

    if user:
        full_name = user[1] or "User"
    else:
        full_name = "User"

    context.user_data["message_user_name"] = full_name

    await update.message.reply_text(
        f"👤 *User Found*\n\n"
        f"Name: *{full_name}*\n"
        f"User ID: `{user_id}`\n\n"
        "📝 Send the message you want to deliver privately.\n\n"
        "You can send:\n"
        "• ✍️ Text\n"
        "• 🖼 Picture with an optional caption\n\n"
        "💡 *Copyable Text*\n"
        "To make a value copyable, put it inside "
        "[square brackets].\n\n"
        "Example:\n"
        "Wallet Address: [0x123456789]\n"
        "Transaction ID: [ABC123456]",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard,
    )

    return MESSAGE


# ==================================================
# RECEIVE ADMIN TEXT MESSAGE
# ==================================================

async def receive_text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.message.text == "❌ Cancel":

        context.user_data.clear()

        await update.message.reply_text(
            "❌ Cancelled.",
            reply_markup=admin_menu,
        )

        return ConversationHandler.END

    message = update.message.text.strip()

    if not message:

        await update.message.reply_text(
            "❌ Message cannot be empty."
        )

        return MESSAGE

    user_id = context.user_data["message_user_id"]

    full_name = context.user_data.get(
        "message_user_name",
        "User",
    )

    try:

        # ------------------------------------------
        # Format copyable sections
        # ------------------------------------------

        formatted_message = (
            format_copyable_message(message)
        )

        # ------------------------------------------
        # Send message to user
        # ------------------------------------------

        sent_message = await context.bot.send_message(
            chat_id=user_id,
            text=(
                "📨 <b>NebuMine Pro Support</b>\n\n"
                f"{formatted_message}"
                f"{REPLY_INSTRUCTIONS}"
            ),
            parse_mode="HTML",
        )

        # ------------------------------------------
        # Save outgoing message → user relationship
        # ------------------------------------------

        admin_message_map[
            sent_message.message_id
        ] = user_id

    except Exception as e:

        print(
            f"Failed to send admin text message "
            f"to {user_id}: {e}"
        )

        await update.message.reply_text(
            "❌ Failed to deliver the message.\n\n"
            "The user may have blocked the bot or "
            "their Telegram account may not be reachable.",
            reply_markup=admin_menu,
        )

        context.user_data.clear()

        return ConversationHandler.END

    await update.message.reply_text(
        "✅ *Message Delivered Successfully!*\n\n"
        f"👤 User: {full_name}\n"
        f"🆔 User ID: `{user_id}`\n\n"
        "The user can reply directly to the message.",
        parse_mode="Markdown",
        reply_markup=admin_menu,
    )

    context.user_data.clear()

    return ConversationHandler.END


# ==================================================
# RECEIVE ADMIN PHOTO
# ==================================================

async def receive_photo_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = context.user_data.get(
        "message_user_id"
    )

    if not user_id:

        await update.message.reply_text(
            "❌ User information was lost.\n\n"
            "Please start the Message User process again.",
            reply_markup=admin_menu,
        )

        context.user_data.clear()

        return ConversationHandler.END

    full_name = context.user_data.get(
        "message_user_name",
        "User",
    )

    photo = update.message.photo[-1]

    caption = update.message.caption or ""

    try:

        # ------------------------------------------
        # Format photo caption
        # ------------------------------------------

        if caption.strip():

            formatted_caption = (
                format_copyable_message(
                    caption.strip()
                )
            )

            outgoing_caption = (
                "📨 <b>NebuMine Pro Support</b>\n\n"
                f"{formatted_caption}"
                f"{REPLY_INSTRUCTIONS}"
            )

        else:

            outgoing_caption = (
                "📨 <b>NebuMine Pro Support</b>"
                f"{REPLY_INSTRUCTIONS}"
            )

        # ------------------------------------------
        # Telegram caption limit
        # ------------------------------------------

        if len(outgoing_caption) > 1024:

            await update.message.reply_text(
                "❌ The photo caption is too long.\n\n"
                "Please shorten the caption and try again.",
                reply_markup=cancel_keyboard,
            )

            return MESSAGE

        # ------------------------------------------
        # Send photo to user
        # ------------------------------------------

        sent_message = await context.bot.send_photo(
            chat_id=user_id,
            photo=photo.file_id,
            caption=outgoing_caption,
            parse_mode="HTML",
        )

        # ------------------------------------------
        # Save outgoing photo message → user
        # ------------------------------------------

        admin_message_map[
            sent_message.message_id
        ] = user_id

    except Exception as e:

        print(
            f"Failed to send admin photo message "
            f"to {user_id}: {e}"
        )

        await update.message.reply_text(
            "❌ Failed to deliver the picture.\n\n"
            "Please try again.",
            reply_markup=admin_menu,
        )

        context.user_data.clear()

        return ConversationHandler.END

    await update.message.reply_text(
        "✅ *Picture Delivered Successfully!*\n\n"
        f"👤 User: {full_name}\n"
        f"🆔 User ID: `{user_id}`\n\n"
        "The user can reply directly to the picture.",
        parse_mode="Markdown",
        reply_markup=admin_menu,
    )

    context.user_data.clear()

    return ConversationHandler.END


# ==================================================
# USER REPLY → ADMIN
# ==================================================

async def user_reply_to_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.message

    if not message:
        return

    # ------------------------------------------
    # Ignore admin messages
    # ------------------------------------------

    if update.effective_user.id == ADMIN_ID:
        return

    # ------------------------------------------
    # Only handle replies
    # ------------------------------------------

    if not message.reply_to_message:
        return

    replied_message_id = (
        message.reply_to_message.message_id
    )

    # ------------------------------------------
    # Find original user
    # ------------------------------------------

    original_user_id = admin_message_map.get(
        replied_message_id
    )

    if not original_user_id:
        return

    # ------------------------------------------
    # Verify sender
    # ------------------------------------------

    if update.effective_user.id != original_user_id:
        return

    user = get_user(original_user_id)

    if user:
        full_name = user[1] or "User"
    else:
        full_name = (
            update.effective_user.full_name
            or "User"
        )

    try:

        # ==========================================
        # USER TEXT REPLY
        # ==========================================

        if message.text:

            user_message = (
                message.text.strip()
            )

            if not user_message:
                return

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "💬 <b>User Reply</b>\n\n"
                    f"👤 User: "
                    f"<b>{escape(full_name)}</b>\n"
                    f"🆔 User ID: "
                    f"<code>{original_user_id}</code>\n\n"
                    "━━━━━━━━━━━━━━━━━━\n\n"
                    f"{escape(user_message)}\n\n"
                    "━━━━━━━━━━━━━━━━━━\n\n"
                    "📨 Use <b>📨 Message User</b> and enter "
                    f"<code>{original_user_id}</code> to reply."
                ),
                parse_mode="HTML",
            )

        # ==========================================
        # USER PHOTO REPLY
        # ==========================================

        elif message.photo:

            photo = message.photo[-1]

            caption = message.caption or ""

            admin_caption = (
                "🖼 <b>User Photo Reply</b>\n\n"
                f"👤 User: "
                f"<b>{escape(full_name)}</b>\n"
                f"🆔 User ID: "
                f"<code>{original_user_id}</code>\n\n"
            )

            if caption.strip():

                admin_caption += (
                    "━━━━━━━━━━━━━━━━━━\n\n"
                    f"💬 {escape(caption.strip())}\n\n"
                    "━━━━━━━━━━━━━━━━━━"
                )

            else:

                admin_caption += (
                    "The user sent a picture "
                    "without a caption."
                )

            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo.file_id,
                caption=admin_caption,
                parse_mode="HTML",
            )

        else:

            return

        # ==========================================
        # CONFIRM TO USER
        # ==========================================

        await message.reply_text(
            "✅ Your message has been sent to "
            "NebuMine Pro Support."
        )

    except Exception as e:

        print(
            f"Failed to forward user reply "
            f"from {original_user_id} to admin: {e}"
        )


# ==================================================
# CANCEL
# ==================================================

async def cancel_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    context.user_data.clear()

    await update.message.reply_text(
        "❌ Message cancelled.",
        reply_markup=admin_menu,
    )

    return ConversationHandler.END


# ==================================================
# ADMIN MESSAGE HANDLER
# ==================================================

admin_message_handler = ConversationHandler(

    entry_points=[
        MessageHandler(
            filters.Regex("^📨 Message User$"),
            start_message_user,
        )
    ],

    states={

        # ------------------------------------------
        # USER ID
        # ------------------------------------------

        USER_ID: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_message_user,
            )
        ],

        # ------------------------------------------
        # MESSAGE CONTENT
        # ------------------------------------------

        MESSAGE: [

            # Text message
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_text_message,
            ),

            # Photo message
            MessageHandler(
                filters.PHOTO,
                receive_photo_message,
            ),

        ],

    },

    fallbacks=[
        MessageHandler(
            filters.Regex("^❌ Cancel$"),
            cancel_message,
        )
    ],
)


# ==================================================
# USER REPLY HANDLER
# ==================================================

user_reply_handler = MessageHandler(
    (
        filters.REPLY
        & (
            filters.TEXT
            | filters.PHOTO
        )
        & ~filters.COMMAND
    ),
    user_reply_to_admin,
)
