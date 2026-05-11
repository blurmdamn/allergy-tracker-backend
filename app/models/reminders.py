from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Reminder(Base):
    """
    Напоминание пользователя.

    repeat_type:
    - none: однократное напоминание
    - daily: ежедневно
    - weekly: еженедельно
    - monthly: ежемесячно

    scheduled_at хранит следующую дату отправки.
    sent_at хранит последнюю дату успешной отправки.
    """

    __tablename__ = "reminders"

    __table_args__ = (
        CheckConstraint(
            "type IN ('daily_checkin', 'asit_visit', 'questionnaire', 'custom')",
            name="ck_reminders_type",
        ),
        CheckConstraint(
            "repeat_type IN ('none', 'daily', 'weekly', 'monthly')",
            name="ck_reminders_repeat_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    type: Mapped[str] = mapped_column(String(32), nullable=False)
    repeat_type: Mapped[str] = mapped_column(
        String(16),
        default="none",
        nullable=False,
    )

    message: Mapped[str] = mapped_column(String(512), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    active_months: Mapped[list[int] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )