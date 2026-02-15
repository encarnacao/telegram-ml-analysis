"""
Application configuration loaded from environment variables.
"""

import os

# Telegram Bot API token (required)
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# Chat ID to monitor (default: -1001378056746)
# Only messages from this chat will be collected
ALLOWED_CHAT_ID = int(os.environ.get("ALLOWED_CHAT_ID", "-1001378056746"))
