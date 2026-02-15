"""
Telegram message handlers.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.services import process_message

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle incoming text messages from the monitored chat.

    Extracts message data, persists to database, and logs to stdout.

    Args:
        update: The Telegram update containing the message.
        context: The callback context (unused).
    """
    message = update.effective_message
    if not message or not message.text:
        return

    if not message.from_user:
        logger.warning("Received message without from_user")
        return

    # Persist message to database
    try:
        process_message(message)
    except Exception as e:
        logger.error("Failed to persist message: %s", e)
        return

    # Log to stdout in the desired format
    username = message.from_user.username or message.from_user.first_name
    text_preview = message.text[:100] + "..." if len(message.text) > 100 else message.text
    text_preview = text_preview.replace("\n", " ")

    print(f" ~ {username} : {text_preview}")
