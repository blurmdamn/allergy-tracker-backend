"""add telegram accounts

Revision ID: a91c2617ade6
Revises: 2c7f453a59ab
Create Date: 2026-05-09 00:32:47.662188

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a91c2617ade6"
down_revision: Union[str, Sequence[str], None] = "2c7f453a59ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "telegram_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=True),
        sa.Column("username", sa.String(length=128), nullable=True),
        sa.Column("first_name", sa.String(length=128), nullable=True),
        sa.Column("link_token", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("linked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id", name="uq_telegram_accounts_chat_id"),
        sa.UniqueConstraint("link_token", name="uq_telegram_accounts_link_token"),
        sa.UniqueConstraint("user_id", name="uq_telegram_accounts_user_id"),
    )

    op.create_index(
        op.f("ix_telegram_accounts_chat_id"),
        "telegram_accounts",
        ["chat_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_telegram_accounts_link_token"),
        "telegram_accounts",
        ["link_token"],
        unique=False,
    )

    op.create_index(
        op.f("ix_telegram_accounts_user_id"),
        "telegram_accounts",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_telegram_accounts_user_id"),
        table_name="telegram_accounts",
    )

    op.drop_index(
        op.f("ix_telegram_accounts_link_token"),
        table_name="telegram_accounts",
    )

    op.drop_index(
        op.f("ix_telegram_accounts_chat_id"),
        table_name="telegram_accounts",
    )

    op.drop_table("telegram_accounts")