"""
Telegram message handlers.
"""

import logging
from os import strerror
from telegram import Update
from telegram.ext import ContextTypes

from app.services import process_message, get_media_type

logger = logging.getLogger(__name__)

text_dict = {
    "photo": "caption",
    "video": "caption",
    "sticker": "emoji",
    "document": "caption",
    "animation": "caption"
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle incoming text messages from the monitored chat.

    Extracts message data, persists to database, and logs to stdout.

    Args:
        update: The Telegram update containing the message.
        context: The callback context (unused).
    """
    message = update.effective_message
    
    if not message:
        return

    media_type = get_media_type(message)
    
    text = ""

    if media_type is not None:
        attr = text_dict.get(media_type)
        text = (getattr(message, attr, "") if attr else "") or ""
    elif message.text:
        text = message.text or ""

    if not text:
        return


    if not message.from_user:
        logger.warning("Received message without from_user")
        return

    # Persist message to database
    try:
        process_message(message, text)
    except Exception as e:
        logger.error("Failed to persist message: %s", e)
        return

    # Log to stdout in the desired format
    username = message.from_user.username or message.from_user.first_name
    text_preview = text[:100] + "..." if len(text) > 100 else text
    text_preview = text_preview.replace("\n", " ")

    print(f" ~ {username} : {text_preview}")
