from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters

from config import ADMIN_ID
from database import user_exists
from keyboards import main_menu, admin_menu

from handlers.navigation import (
    clear_navigation,
    push_page,
)


# =====================================
# UNREGISTERED USER MENU
# =====================================

unregistered_menu = ReplyKeyboardMarkup(
    [
        ["🆕 New User Registration"],
        ["💬 Chat with Support"],
        ["ℹ️ Help"],
    ],
    resize_keyboard=True,
)


# =====================================
# SHOW MAIN MENU
# =====================================

async def show_main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    print("========== MAIN MENU OPENED ==========")

    # Reset navigation
    clear_navigation(context)

    push_page(context, "main_menu")

    print(
        "Navigation Stack:",
        context.user_data.get("navigation_stack"),
    )

    print("======================================")

    user_id = update.effective_user.id

    # =====================================
    # ADMIN
    # =====================================

    if user_id == ADMIN_ID:

        keyboard = admin_menu

    # =====================================
    # REGISTERED USER
    # =====================================

    elif user_exists(user_id):

        keyboard = main_menu

    # =====================================
    # UNREGISTERED USER
    # =====================================

    else:

        keyboard = unregistered_menu

    await update.message.reply_text(
        "🏠 Main Menu",
        reply_markup=keyboard,
    )


# =====================================
# MAIN MENU HANDLER
# =====================================

main_menu_handler = MessageHandler(
    filters.Regex("^🏠 Main Menu$"),
    show_main_menu,
)
