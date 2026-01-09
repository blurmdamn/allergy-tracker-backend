from __future__ import annotations

from datetime import date
from sqlalchemy import String, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PatientProfile(Base):
    """
    Профиль пациента (отдельно от User).
    У врача можно будет сделать DoctorProfile позже, если понадобится.
    """
    __tablename__ = "patient_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # "female" | "male" | "other" (или можно хранить "F/M/O")
    sex: Mapped[str | None] = mapped_column(String(16), nullable=True)
