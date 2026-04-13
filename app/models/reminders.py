from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Reminder(Base):
    """
    Напоминания.
    type: "asit_visit" | "daily_checkin" | "questionnaire" | "custom"
    active_months хранит сезонность правила напоминания.
    """
    __tablename__ = "reminders"
    __table_args__ = (
        CheckConstraint(
            "type IN ('asit_visit', 'daily_checkin', 'questionnaire', 'custom')",
            name="ck_reminders_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    type: Mapped[str] = mapped_column(String(32))
    message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    # сезонность: [1..12], None => всегда активно
    active_months: Mapped[list[int] | None] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
