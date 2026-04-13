from __future__ import annotations

from datetime import date

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Table, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


patient_allergen = Table(
    "patient_allergen",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("allergen_id", ForeignKey("allergens.id"), primary_key=True),
)


patient_symptom = Table(
    "patient_symptom",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("symptom_id", ForeignKey("symptoms.id"), primary_key=True),
)


class PatientAllergy(Base):
    __tablename__ = "patient_allergy"
    __table_args__ = (
        CheckConstraint(
            "frequency IS NULL OR frequency IN ('contact_only', 'daily')",
            name="ck_patient_allergy_frequency",
        ),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    # когда впервые появились симптомы
    symptoms_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # частота: "contact_only" | "daily"
    frequency: Mapped[str | None] = mapped_column(String(32), nullable=True)


class PatientAllergyMonth(Base):
    __tablename__ = "patient_allergy_months"
    __table_args__ = (
        CheckConstraint("month_no BETWEEN 1 AND 12", name="ck_patient_allergy_months_month_no"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("patient_allergy.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    month_no: Mapped[int] = mapped_column(Integer, primary_key=True)
