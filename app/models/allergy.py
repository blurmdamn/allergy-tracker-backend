from __future__ import annotations

from datetime import date
from sqlalchemy import ForeignKey, Date, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

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

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    # когда впервые появились симптомы
    symptoms_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # сезонность (мультивыбор): месяцы 1..12
    # пример: весна+начало лета => [3,4,5,6]
    active_months: Mapped[list[int] | None] = mapped_column(JSONB, nullable=True)

    # частота: "contact_only" | "daily"
    frequency: Mapped[str | None] = mapped_column(String(32), nullable=True)
