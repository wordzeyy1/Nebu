from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters


async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = """
🔒 *Privacy Policy*

━━━━━━━━━━━━━━━━━━

Your privacy is important to us.

We collect only the information required to operate your Nebumine pro account safely.

━━━━━━━━━━━━━━━━━━

📄 Information We Collect

• Name
• Email Address
• Phone Number
• Country
• Wallet Address
• KYC Documents

━━━━━━━━━━━━━━━━━━

🔐 Security

All personal information is securely stored and protected against unauthorized access.

━━━━━━━━━━━━━━━━━━

🪪 KYC Documents

Your KYC documents are used solely for identity verification and regulatory compliance.

━━━━━━━━━━━━━━━━━━

🚫 Data Sharing

We never sell or share your personal information with third parties for marketing purposes.

━━━━━━━━━━━━━━━━━━

📊 Transaction Records

Your deposits, withdrawals and mining activities are securely recorded to protect your account.

━━━━━━━━━━━━━━━━━━

By using Nebumine pro Cloud Mining, you agree to this Privacy Policy.
"""

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
    )


privacy_handler = MessageHandler(
    filters.Regex("^🔒 Privacy Policy$"),
    privacy,
)
