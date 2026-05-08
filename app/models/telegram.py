from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TelegramAccount(Base):
    """
    Привязка пользователя приложения к Telegram.

    link_token нужен для deep link:
    https://t.me/<bot_username>?start=<link_token>

    chat_id сохраняется после того, как пользователь нажал Start в боте.
    """

    __tablename__ = "telegram_accounts"

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_telegram_accounts_user_id"),
        UniqueConstraint("chat_id", name="uq_telegram_accounts_chat_id"),
        UniqueConstraint("link_token", name="uq_telegram_accounts_link_token"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)

    username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    link_token: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    linked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )