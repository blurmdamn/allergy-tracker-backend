from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AsitPlan(Base):
    """
    План АСИТ.
    regimen: "conventional" | "daily" | "accelerated"
    """
    __tablename__ = "asit_plans"
    __table_args__ = (
        CheckConstraint(
            "regimen IN ('conventional', 'daily', 'accelerated')",
            name="ck_asit_plans_regimen",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    regimen: Mapped[str] = mapped_column(String(32))
    target_allergen_id: Mapped[int | None] = mapped_column(ForeignKey("allergens.id"), nullable=True)
    medication_id: Mapped[int | None] = mapped_column(ForeignKey("medications.id"), nullable=True)
    interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dose_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)

    started_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AsitEvent(Base):
    """
    События АСИТ (календарь): плановая дата и фактическая дата приёма/введения.
    status: "planned" | "done" | "skipped" | "rescheduled"
    """
    __tablename__ = "asit_events"
    __table_args__ = (
        CheckConstraint(
            "status IN ('planned', 'done', 'skipped', 'rescheduled')",
            name="ck_asit_events_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("asit_plans.id"), index=True)

    planned_date: Mapped[date] = mapped_column(Date, index=True)
    actual_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    dose_value: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="planned")
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
