from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PatientMedication(Base):
    """
    Текущее лечение пациента (активные/неактивные курсы).
    medication_id → справочник medications.

    treatment_effect:
    - good    — хороший успех
    - partial — частичный успех
    - none    — неуспех

    Это общий эффект текущего лечения, НЕ факт приёма препарата.
    Фактические приёмы хранятся отдельно в MedicationIntakeLog.
    """

    __tablename__ = "patient_medications"

    __table_args__ = (
        CheckConstraint(
            "treatment_effect IS NULL OR treatment_effect IN ('good', 'partial', 'none')",
            name="ck_patient_medications_treatment_effect",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    medication_id: Mapped[int] = mapped_column(ForeignKey("medications.id"), index=True)

    # курс
    started_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    ended_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # дозировка/режим
    dose_text: Mapped[str | None] = mapped_column(String(64), nullable=True)
    times_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interval_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # общий эффект текущего лечения
    treatment_effect: Mapped[str | None] = mapped_column(String(16), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MedicationIntakeLog(Base):
    """
    Запись о фактическом приёме препарата.
    effect: "good" | "partial" | "none"
    """

    __tablename__ = "medication_intake_logs"

    __table_args__ = (
        CheckConstraint(
            "effect IS NULL OR effect IN ('good', 'partial', 'none')",
            name="ck_medication_intake_logs_effect",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    patient_medication_id: Mapped[int] = mapped_column(
        ForeignKey("patient_medications.id"),
        index=True,
    )

    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # количество единиц за конкретную отметку/приём
    dose_taken: Mapped[int | None] = mapped_column(Integer, nullable=True)
    effect: Mapped[str | None] = mapped_column(String(16), nullable=True)
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)