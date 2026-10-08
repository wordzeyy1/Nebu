from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from handlers.navigation import push_page

from keyboards import deposit_cancel_keyboard

from handlers.conversation_cancel import cancel_conversation

from utils.prices import get_prices
from utils.qrcode_generator import generate_qr

AMOUNT = 0

submit_keyboard = ReplyKeyboardMarkup(
    [
        ["📤 Submit Transaction Hash"],
        ["🏠 Main Menu"],
    ],
    resize_keyboard=True,
)

# ---------------- BTC ----------------

async def select_btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("from_back", False):
        push_page(context, "deposit")
    context.user_data["network"] = "BTC"

    await update.message.reply_text(
        "💵 Enter the amount you want to deposit in USD.\n\nExample:\n250",
        reply_markup=deposit_cancel_keyboard,
    )

    return AMOUNT


# ---------------- ETH ----------------

async def select_eth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("from_back", False):
        push_page(context, "deposit")
    context.user_data["network"] = "ETH"

    await update.message.reply_text(
        "💵 Enter the amount you want to deposit in USD.\n\nExample:\n250",
        reply_markup=deposit_cancel_keyboard,
    )

    return AMOUNT


# ---------------- USDT TRC20 ----------------

async def select_usdt_trc20(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("from_back", False):
        push_page(context, "deposit")
    context.user_data["network"] = "USDT TRC20"

    await update.message.reply_text(
        "💵 Enter the amount you want to deposit in USD.\n\nExample:\n250",
        reply_markup=deposit_cancel_keyboard,
    )

    return AMOUNT


# ---------------- USDT ERC20 ----------------

async def select_usdt_erc20(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("from_back", False):
        push_page(context, "deposit")
    context.user_data["network"] = "USDT ERC20"

    await update.message.reply_text(
        "💵 Enter the amount you want to deposit in USD.\n\nExample:\n250",
        reply_markup=deposit_cancel_keyboard,
    )

    return AMOUNT


# ---------------- USDC ERC20 ----------------

async def select_usdc_erc20(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("from_back", False):
        push_page(context, "deposit")
    context.user_data["network"] = "USDC ERC20"

    await update.message.reply_text(
        "💵 Enter the amount you want to deposit in USD.\n\nExample:\n250",
        reply_markup=deposit_cancel_keyboard,
    )

    return AMOUNT


# ---------------- RECEIVE USD AMOUNT ----------------

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
        
    try:
        usd_amount = float(update.message.text)

        if usd_amount <= 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid USD amount."
        )
        return AMOUNT

    network = context.user_data["network"]

    addresses = {
        "BTC": "bc1qhnxdrmy2jpdmnguk8gk2f4dhdsmr9kct2c84c8",
        "ETH": "0x8EfE5CeCA00ca07E913EbabCaF6b79e044214Dc5",
        "USDT TRC20": "TEr5rD8xZT4P6DebZcRe5JDcpoCXPF5QLH",
        "USDT ERC20": "0x8EfE5CeCA00ca07E913EbabCaF6b79e044214Dc5",
        "USDC ERC20": "0x8EfE5CeCA00ca07E913EbabCaF6b79e044214Dc5",
    }

    symbols = {
        "BTC": "BTC",
        "ETH": "ETH",
        "USDT TRC20": "USDT",
        "USDT ERC20": "USDT",
        "USDC ERC20": "USDC",
    }

    print("Selected Network:", network)
    print("Wallet Address:", addresses[network])

    prices = get_prices()

    price = prices.get(network)

    if price is None:
        await update.message.reply_text(
            "❌ Unable to retrieve live prices.\nPlease try again later."
        )
        return ConversationHandler.END

    crypto_amount = usd_amount / price

    context.user_data["usd_amount"] = usd_amount
    context.user_data["crypto_amount"] = crypto_amount

    qr_file = generate_qr(
        network,
        addresses[network],
        crypto_amount,
    )

    with open(qr_file, "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=f"""
💳 *Deposit Details*

💵 Deposit Value:
${usd_amount:,.2f}

🌐 Network:
{network}

📈 Current Price:
${price:,.2f}

🪙 Send Exactly:

`{crypto_amount:.8f} {symbols[network]}`

📥 Deposit Address:

`{addresses[network]}`

📱 Scan the QR code with a compatible wallet (e.g. Trust Wallet).

If your wallet reports **"Chain not supported"**, copy the wallet address above and paste it manually into your wallet.

━━━━━━━━━━━━━━

1️⃣ Send exactly the amount shown above.

2️⃣ After completing the transfer, copy your Transaction Hash (TXID).

3️⃣ Click **📤 Submit Transaction Hash**.

4️⃣ Paste your TXID.

⚠️ Send only **{symbols[network]}** through the selected network.

⚠️ Sending funds through the wrong network may result in permanent loss of funds.
""",
            parse_mode="Markdown",
            reply_markup=submit_keyboard,
        )

    return ConversationHandler.END


deposit_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex("^₿ BTC$"), select_btc),
        MessageHandler(filters.Regex("^♦ ETH$"), select_eth),
        MessageHandler(filters.Regex("^💲 USDT \\(TRC20\\)$"), select_usdt_trc20),
        MessageHandler(filters.Regex("^💲 USDT \\(ERC20\\)$"), select_usdt_erc20),
        MessageHandler(filters.Regex("^💲 USDC \\(ERC20\\)$"), select_usdc_erc20),
    ],
    states={
    AMOUNT: [
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & ~filters.Regex(r"^❌ Cancel$"),
            get_amount,
        )
    ]
},  
    fallbacks=[
    MessageHandler(
        filters.Regex("^🏠 Main Menu$"),
        cancel_conversation,
    ),
    MessageHandler(
        filters.Regex("^❌ Cancel$"),
        cancel_conversation,
    ),
]
)
allow_reentry=True,
