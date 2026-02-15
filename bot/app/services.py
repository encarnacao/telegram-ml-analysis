"""
Business logic services for message processing and persistence.
"""

import logging
from telegram import Message as TelegramMessage
from sqlalchemy.dialects.postgresql import insert

from app.database import SessionLocal
from app.models import Chat, Message, User

logger = logging.getLogger(__name__)


def process_message(tg_message: TelegramMessage) -> None:
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

            # Insert message - ignore duplicates
            msg_stmt = (
                insert(Message)
                .values(
                    telegram_message_id=tg_message.message_id,
                    chat_id=tg_message.chat.id,
                    user_id=tg_message.from_user.id,
                    text=tg_message.text,
                    date=tg_message.date,
                )
                .on_conflict_do_nothing(constraint="uq_message_chat")
            )
            result = db.execute(msg_stmt)

            db.commit()

            if result.rowcount > 0:
                logger.debug(
                    "Saved message %d from user %d",
                    tg_message.message_id,
                    tg_message.from_user.id,
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
