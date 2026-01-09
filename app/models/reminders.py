from __future__ import annotations

from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base


class Reminder(Base):
    """
    Напоминания:
    type: "asit_visit" | "daily_checkin" | "questionnaire" | "custom"
    scheduled_at: когда должно сработать (первый раз)
    active_months: сезонность (например [3,4,5,6] для весна+начало лета)
      - None => всегда активно
    """
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    type: Mapped[str] = mapped_column(String(32))
    message: Mapped[str | None] = mapped_column(String(512), nullable=True)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    # сезонность: [1..12]
    active_months: Mapped[list[int] | None] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
