from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import ForeignKey, Integer, String, DateTime, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PatientMedication(Base):
    """
    Текущее лечение пациента (активные/неактивные курсы).
    medication_id → справочник medications.
    """
    __tablename__ = "patient_medications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    medication_id: Mapped[int] = mapped_column(ForeignKey("medications.id"), index=True)

    # курс
    started_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    ended_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # дозировка/режим (гибко)
    dose_text: Mapped[str | None] = mapped_column(String(64), nullable=True)     # "10 mg"
    times_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)   # 1/2/3...
    interval_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)  # если важно

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MedicationIntakeLog(Base):
    """
    Опрос по таблеткам при клике:
    - tablets_per_day
    - effect: "success" | "partial" | "fail"
    """
    __tablename__ = "medication_intake_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    patient_medication_id: Mapped[int] = mapped_column(
        ForeignKey("patient_medications.id"),
        index=True
    )

    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tablets_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    effect: Mapped[str | None] = mapped_column(String(16), nullable=True)

    note: Mapped[str | None] = mapped_column(String(512), nullable=True)
