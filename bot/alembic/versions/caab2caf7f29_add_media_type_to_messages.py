"""add media_type to messages

Revision ID: caab2caf7f29
Revises: 9ff6349a3fd5
Create Date: 2026-02-16 15:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'caab2caf7f29'
down_revision: Union[str, None] = '9ff6349a3fd5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('messages', sa.Column('media_type', sa.String(20), nullable=True))
    op.create_index('ix_messages_media_type', 'messages', ['media_type'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_messages_media_type', table_name='messages')
    op.drop_column('messages', 'media_type')
