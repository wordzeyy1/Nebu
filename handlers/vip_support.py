import asyncio

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import SUPPORT_USERNAME

from keyboards import main_menu


async def vip_support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    first_name = update.effective_user.first_name or "Investor"

    # ==========================
    # Live Connection Animation
    # ==========================

    status = await update.message.reply_text(
        "🔄 Connecting to Nebumine pro Customer Support..."
    )

    await asyncio.sleep(1)

    await status.edit_text(
        "🔍 Verifying your account..."
    )

    await asyncio.sleep(1)

    await status.edit_text(
        "👤 Assigning your dedicated Customer Support Representative..."
    )

    await asyncio.sleep(1)

    await status.edit_text(
        "✅ *Connection Successful!*\n\n"
        "Your VIP Customer Support Representative is now ready to assist you.",
        parse_mode="Markdown",
    )

    await asyncio.sleep(1)

    await status.edit_text(
        "💬 Preparing your secure support session..."
    )

    await asyncio.sleep(2)

    representative_id = f"CS-{update.effective_user.id % 100000:05d}"
    support_reference = f"QTS-{update.effective_user.id % 1000000:06d}"

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "👨‍💼 Start Secure Chat",
                    url=f"https://t.me/{SUPPORT_USERNAME}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Main Menu",
                    callback_data="vip_support_main_menu",
                )
            ],
        ]
    )

    await update.message.reply_text(
        f"""
━━━━━━━━━━━━━━━━━━

👨‍💼 *Customer Support Representative Joined*

Hello *{first_name}* 👋

Welcome to *Nebumine pro*.

My name is *Nebumine pro Customer Support*.

I have been assigned as your dedicated Customer Support Representative and I'll personally assist you throughout your Nebumine Pro journey.

━━━━━━━━━━━━━━━━━━

👤 *Representative*

Nebumine pro Customer Support 

🆔 *Representative ID*

`{representative_id}`

🎫 *Support Reference*

`{support_reference}`

━━━━━━━━━━━━━━━━━━

🟢 *Secure Support Session*

Status:
*Active*

Encryption:
*Enabled 🔒*

Priority:
*VIP Miner Support*

Representative:
*Online*

━━━━━━━━━━━━━━━━━━

Your dedicated representative can assist you with:

✅ Deposit Verification

✅ Withdrawal Assistance

✅ Cloud Mining Support

✅ Refund request process 

✅ Referral Program

✅ KYC Verification

✅ Wallet & Account Issues

✅ Technical Assistance

━━━━━━━━━━━━━━━━━━

🔒 *Security Reminder*

For your protection, official Nebumine pro representatives will **never** request:

• Telegram Password

• Login Verification Codes

• Wallet Private Keys

• Recovery Phrase / Seed Phrase

• Remote Access to your Device

Always communicate only through the official support channel below.

━━━━━━━━━━━━━━━━━━

🏆 *Premium Digital Asset Platform*

Your success is our priority.

Thank you for choosing *Nebumine pro*.
""",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def vip_support_main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    await query.message.reply_text(
        "🏠 Main Menu",
        reply_markup=main_menu,
    )


vip_support_handler = MessageHandler(
    filters.Regex("^💬 Chat with Support$"),
    vip_support,
)

vip_support_main_menu_handler = CallbackQueryHandler(
    vip_support_main_menu,
    pattern="^vip_support_main_menu$",
    )
