"""
Telegram ML Analysis Bot - Entry Point.

Monitors a Telegram group for text messages and stores them in PostgreSQL
for later machine learning analysis.
"""

import logging
import sys

from telegram.ext import Application, MessageHandler, filters

from app.config import ALLOWED_CHAT_ID, TELEGRAM_BOT_TOKEN
from app.handlers import handle_message


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
        stream=sys.stdout,
    )
    # Reduce noise from httpx (used by python-telegram-bot)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def main() -> None:
    """Initialize and run the Telegram bot."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Telegram ML Analysis Bot")
    logger.info("Monitoring chat ID: %d", ALLOWED_CHAT_ID)

    # Build the application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Filter: only text messages (not commands) from the allowed chat
    chat_filter = filters.Chat(chat_id=ALLOWED_CHAT_ID)

    # Register handler
    application.add_handler(
        MessageHandler(chat_filter, handle_message)
    )

    logger.info("Bot handlers registered, starting polling...")

    # Start polling for messages
    application.run_polling(
        allowed_updates=["message"],
        drop_pending_updates=True,  # Ignore messages sent while bot was offline
    )


if __name__ == "__main__":
    main()
