"""add repeat type and telegram language

Revision ID: 79f0aa0c83e7
Revises: a91c2617ade6
Create Date: 2026-05-09 01:18:39.415197

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "79f0aa0c83e7"
down_revision: Union[str, Sequence[str], None] = "a91c2617ade6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Добавляем repeat_type временно nullable,
    # чтобы не сломать уже существующие строки reminders.
    op.add_column(
        "reminders",
        sa.Column("repeat_type", sa.String(length=16), nullable=True),
    )

    # 2. Старым напоминаниям ставим значение по умолчанию.
    op.execute(
        "UPDATE reminders SET repeat_type = 'none' WHERE repeat_type IS NULL"
    )

    # 3. Теперь делаем колонку обязательной.
    op.alter_column(
        "reminders",
        "repeat_type",
        existing_type=sa.String(length=16),
        nullable=False,
    )

    # 4. Ограничиваем допустимые значения.
    op.create_check_constraint(
        "ck_reminders_repeat_type",
        "reminders",
        "repeat_type IN ('none', 'daily', 'weekly', 'monthly')",
    )

    # 5. Добавляем язык Telegram-пользователя.
    op.add_column(
        "telegram_accounts",
        sa.Column("language_code", sa.String(length=16), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("telegram_accounts", "language_code")

    op.drop_constraint(
        "ck_reminders_repeat_type",
        "reminders",
        type_="check",
    )

    op.drop_column("reminders", "repeat_type")