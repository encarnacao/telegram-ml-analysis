"""
Business logic services for message processing and persistence.
"""

import logging
from typing import Optional

from telegram import Message as TelegramMessage
from sqlalchemy.dialects.postgresql import insert

from app.database import SessionLocal
from app.models import Chat, Message, User

logger = logging.getLogger(__name__)


def get_media_type(tg_message: TelegramMessage) -> Optional[str]:
    """
    Extract media type from a Telegram message.

    Returns the type of media attached to the message, or None if no media.
    Checks in order of most to least common types.
    """
    if tg_message.photo:
        return "photo"
    if tg_message.video:
        return "video"
    if tg_message.sticker:
        return "sticker"
    if tg_message.animation:  # GIFs
        return "animation"
    if tg_message.document:
        return "document"
    return None


def process_message(tg_message: TelegramMessage, text: str) -> None:
    """
    Process and persist a Telegram message.

    Performs upsert for user and chat, then inserts the message.
    Duplicates are ignored via ON CONFLICT DO NOTHING.

    Args:
        tg_message: The Telegram message object to process.
    """
    if not tg_message.from_user:
        logger.warning("Message without from_user, skipping")
        return

    with SessionLocal() as db:
        try:
            # Upsert user - update name/username if changed
            user_stmt = (
                insert(User)
                .values(
                    id=tg_message.from_user.id,
                    username=tg_message.from_user.username,
                    first_name=tg_message.from_user.first_name or "Unknown",
                    last_name=tg_message.from_user.last_name,
                )
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "username": tg_message.from_user.username,
                        "first_name": tg_message.from_user.first_name or "Unknown",
                        "last_name": tg_message.from_user.last_name,
                    },
                )
            )
            db.execute(user_stmt)

            # Upsert chat - update title if changed
            chat_stmt = (
                insert(Chat)
                .values(
                    id=tg_message.chat.id,
                    title=tg_message.chat.title or "Private",
                    chat_type=tg_message.chat.type,
                )
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "title": tg_message.chat.title or "Private",
                        "chat_type": tg_message.chat.type,
                    },
                )
            )
            db.execute(chat_stmt)

            # Extract reply_to_message_id if this is a reply
            reply_to_message_id = None
            if tg_message.reply_to_message:
                reply_to_message_id = tg_message.reply_to_message.message_id

            # Extract media type if present
            media_type = get_media_type(tg_message)

            # Insert message - ignore duplicates
            msg_stmt = (
                insert(Message)
                .values(
                    telegram_message_id=tg_message.message_id,
                    chat_id=tg_message.chat.id,
                    user_id=tg_message.from_user.id,
                    text=text,
                    date=tg_message.date,
                    reply_to_message_id=reply_to_message_id,
                    media_type=media_type,
                )
                .on_conflict_do_nothing(constraint="uq_message_chat")
            )
            result = db.execute(msg_stmt)

            db.commit()

            if result.rowcount > 0:
                reply_info = f" (reply to {reply_to_message_id})" if reply_to_message_id else ""
                media_info = f" [{media_type}]" if media_type else ""
                logger.debug(
                    "Saved message %d from user %d%s%s",
                    tg_message.message_id,
                    tg_message.from_user.id,
                    reply_info,
                    media_info,
                )
            else:
                logger.debug(
                    "Message %d already exists, skipped",
                    tg_message.message_id,
                )

        except Exception as e:
            logger.error("Failed to process message: %s", e)
            db.rollback()
            raise
