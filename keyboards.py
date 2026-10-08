from telegram import ReplyKeyboardMarkup

# ==========================
# USER MAIN MENU
# ==========================
main_menu = ReplyKeyboardMarkup(
    [
        ["🆕 New User Registration"],
        ["💼 Wallet", "🪙⛏ Crypto Cloud Mining"],
        ["👥 Referrals", "🪪 KYC Status"],
        ["📤 Submit KYC", "💰 Submit Refund Request"],
        ["📊 Check Status", "💬 Chat with Support"],
        ["📋 My Profile"],
        ["ℹ️ Help"],
    ],
    resize_keyboard=True
)

# ==========================
# ADMIN MAIN MENU
# ==========================
admin_menu = ReplyKeyboardMarkup(
    [
        ["🆕 New User Registration"],
        ["💼 Wallet", "🪙⛏ Crypto Cloud Mining"],
        ["👥 Referrals", "🪪 KYC Status"],
        ["📤 Submit KYC", "💰 Submit Refund Request"],
        ["📊 Check Status", "💬 Chat with Support"],
        ["📋 My Profile"],
        ["🛠 Admin Panel"],
        ["ℹ️ Help"],
    ],
    resize_keyboard=True
)

# ==========================
# WALLET MENU
# ==========================
wallet_menu = ReplyKeyboardMarkup(
    [
        ["📥 Fund Wallet"],
        ["💸 Withdraw Funds"],
        ["🏦 Change Withdrawal Address"],
        ["📜 Transaction History"],
        ["📋 Withdrawal History"],
        ["🔙 Back"],
        ["🏠 Main Menu"],
    ],
    resize_keyboard=True,
)

# ==========================
# FUND WALLET MENU
# ==========================
fund_keyboard = ReplyKeyboardMarkup(
    [
        ["₿ BTC"],
        ["♦ ETH"],
        ["💲 USDT (TRC20)"],
        ["💲 USDT (ERC20)"],
        ["💲 USDC (ERC20)"],
        ["🔙 Back"],
    ],
    resize_keyboard=True,
)

# ==========================
# HELP MENU
# ==========================

help_menu = ReplyKeyboardMarkup(
    [
        ["📖 FAQs"],
        ["📜 Terms & Conditions"],
        ["🔒 Privacy Policy"],
        ["💬 Contact Support"],
        ["🏠 Main Menu"],
    ],
    resize_keyboard=True,
)

# ==========================
# CANCEL MENU
# ==========================
cancel_menu = ReplyKeyboardMarkup(
    [
        ["🏠 Main Menu"],
        ["❌ Cancel"],
    ],
    resize_keyboard=True
)
# ==========================
# DEPOSIT CANCEL MENU
# ==========================
deposit_cancel_keyboard = ReplyKeyboardMarkup(
    [
        ["❌ Cancel"],
    ],
    resize_keyboard=True,
)
