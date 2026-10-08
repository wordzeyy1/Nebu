from telegram import Update
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

from telegram import ReplyKeyboardMarkup

from config import ADMIN_ID

from handlers.navigation import clear_navigation, push_page

from handlers.main_menu import show_main_menu

from database import (
    add_user,
    user_exists,
    get_referrer,
    set_referrer,
    increment_referrals,
    add_referral_bonus,
)

from keyboards import (
    main_menu,
    admin_menu,
)

cancel_keyboard = ReplyKeyboardMarkup(
    [
        ["❌ Cancel"],
    ],
    resize_keyboard=True,
)

NAME, EMAIL, PHONE, COUNTRY = range(4)
# =====================================
# REGISTRATION GUARD
# =====================================

MENU_BUTTONS = {
    "🏠 Main Menu",

    "🪙⛏ Crypto Cloud Mining",
    "🆕 New User Registration",
    "💼 Wallet",
    "📋 My Profile",
    "📤 Submit KYC",
    "💰 Submit Refund Request",
    "📊 Check Status",
    "👥 Referrals",
    "🪪 KYC Status",
    "💬 Chat with Support",
    "ℹ️ Help",

    "💳 Fund Wallet",
    "📥 Submit Deposit",
    "📜 Transaction History",

    "🛠 Admin Panel",
}

async def registration_guard(update, state):

    if update.message.text in MENU_BUTTONS:

        await update.message.reply_text(
            "⚠️ You are currently completing your account registration.\n\n"
            "Please complete your registration first or tap ❌ Cancel."
        )

        return state

    return None

# =====================================
# START REGISTRATION
# =====================================

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    print(f"Telegram User ID: {update.effective_user.id}")
    
    print(f"User exists: {user_exists(update.effective_user.id)}")
    
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)

    if user_exists(update.effective_user.id):
        await update.message.reply_text(
            "✅ You are already registered.",
            reply_markup=(
                admin_menu
                if update.effective_user.id == ADMIN_ID
                else main_menu
            ),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Enter your Full Name:",
        reply_markup=cancel_keyboard,
    )

    return NAME

# =====================================
# NAME
# =====================================

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)

    guard = await registration_guard(update, NAME)

    if guard is not None:
        return guard

    context.user_data["name"] = update.message.text

    await update.message.reply_text(
        "Enter your Email:",
        reply_markup=cancel_keyboard,
    )

    return EMAIL

# =====================================
# EMAIL
# =====================================

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)

    guard = await registration_guard(update, EMAIL)

    if guard is not None:
        return guard

    context.user_data["email"] = update.message.text

    await update.message.reply_text(
        "Enter your Phone Number:",
        reply_markup=cancel_keyboard,
    )

    return PHONE


# =====================================
# PHONE
# =====================================

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)

    guard = await registration_guard(update, PHONE)

    if guard is not None:
        return guard

    phone = update.message.text.strip()

    # Accept only digits
    if not phone.isdigit():

        await update.message.reply_text(
            "❌ Invalid phone number.\n\n"
            "Please enter digits only.\n\n"
            "Example:\n"
            "+16802734132"
        )

        return PHONE

    # Optional length validation
    if len(phone) < 7 or len(phone) > 15:

        await update.message.reply_text(
            "❌ Invalid phone number length.\n\n"
            "Please enter a valid phone number."
        )

        return PHONE

    context.user_data["phone"] = phone

    await update.message.reply_text(
        "Enter your Country:",
        reply_markup=cancel_keyboard,
    )

    return COUNTRY


# =====================================
# COUNTRY / FINISH REGISTRATION
# =====================================

async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)
    guard = await registration_guard(update, COUNTRY)

    if guard is not None:
        return guard

    user_id = update.effective_user.id
    full_name = context.user_data["name"]
    email = context.user_data["email"]
    phone = context.user_data["phone"]
    country = update.message.text

    print("USER DATA:", context.user_data)
    print("REFERRER:", context.user_data.get("referrer_id"))
    
    # Save user
    add_user(
        user_id,
        full_name,
        email,
        phone,
        country,
    )

    # Handle referral
    if "referrer_id" in context.user_data:

        referrer_id = context.user_data["referrer_id"]

        # Prevent self-referral
        if referrer_id != user_id:

            # Only assign a referrer once
            if get_referrer(user_id) is None:

                set_referrer(user_id, referrer_id)
                increment_referrals(referrer_id)

                # Optional signup bonus
                # add_referral_bonus(referrer_id, 10)

    # Notify admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🆕 *NEW USER REGISTRATION*\n\n"
                f"👤 *Full Name:* {full_name}\n"
                f"🆔 *Telegram ID:* `{user_id}`\n"
                f"📧 *Email:* {email}\n"
                f"📱 *Phone:* {phone}\n"
                f"🌍 *Country:* {country}"
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        print(f"Failed to notify admin: {e}")

    # Notify user
    await update.message.reply_text(
    "🎉 Registration completed successfully!"
    )

    await show_main_menu(update, context)

    # Remove only temporary registration data
    context.user_data.pop("name", None)
    context.user_data.pop("email", None)
    context.user_data.pop("phone", None)
    context.user_data.pop("referrer_id", None)

    return ConversationHandler.END


# =====================================
# CANCEL
# =====================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.pop("name", None)
    context.user_data.pop("email", None)
    context.user_data.pop("phone", None)
    context.user_data.pop("referrer_id", None)

    await update.message.reply_text(
        "❌ Registration cancelled.",
        reply_markup=(
            admin_menu
            if update.effective_user.id == ADMIN_ID
            else main_menu
        ),
    )

    return ConversationHandler.END


# =====================================
# CONVERSATION HANDLER
# =====================================

registration_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex("^🆕 New User Registration$"),
            register,
        )
    ],
    states={
        NAME: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                name,
            )
        ],
        EMAIL: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                email,
            )
        ],
        PHONE: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                phone,
            )
        ],
        COUNTRY: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                country,
            )
        ],
    },
    fallbacks=[
        MessageHandler(
            filters.Regex("^❌ Cancel$"),
            cancel,
        ),
    ],
)
