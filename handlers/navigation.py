from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)

from handlers.page_registry import get_page

STACK_KEY = "navigation_stack"


# =====================================
# STACK FUNCTIONS
# =====================================

def get_stack(context: ContextTypes.DEFAULT_TYPE):

    if STACK_KEY not in context.user_data:
        context.user_data[STACK_KEY] = []

    return context.user_data[STACK_KEY]


def push_page(context: ContextTypes.DEFAULT_TYPE, page: str):

    stack = get_stack(context)

    # Prevent duplicate consecutive pages
    if not stack or stack[-1] != page:
        stack.append(page)


def current_page(context: ContextTypes.DEFAULT_TYPE):

    stack = get_stack(context)

    if stack:
        return stack[-1]

    return None


def previous_page(context: ContextTypes.DEFAULT_TYPE):

    stack = get_stack(context)

    if len(stack) >= 2:
        return stack[-2]

    return None


def clear_navigation(context: ContextTypes.DEFAULT_TYPE):

    context.user_data[STACK_KEY] = []


# =====================================
# UNIVERSAL BACK
# =====================================

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):

    print("========== BACK HANDLER EXECUTED ==========")
    print("Current user_data:", context.user_data)

    stack = get_stack(context)

    print("Current Navigation Stack:", stack)

    # Already at root
    if len(stack) <= 1:

        print("Already at Main Menu")

        await update.message.reply_text(
            "🏠 You are already on the Main Menu."
        )
        return

    # Remove current page
    removed_page = stack.pop()

    print("Removed Page:", removed_page)
    print("Navigation Stack After Pop:", stack)

    # Previous page
    page = stack[-1]

    print("Returning To:", page)

    # Tell handlers Back was used
    context.user_data["from_back"] = True

    handler = get_page(page)

    if handler:
        await handler(update, context)
    else:
        print("ERROR: No handler registered for", page)

        await update.message.reply_text(
            "❌ Previous page could not be restored."
        )

    # Reset flag
    context.user_data["from_back"] = False

    print("========== BACK COMPLETE ==========")


# =====================================
# GLOBAL BACK HANDLER
# =====================================

back_handler = MessageHandler(
    filters.Regex("^🔙 Back$"),
    go_back,
    )
