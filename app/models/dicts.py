from __future__ import annotations

from sqlalchemy import String, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Allergen(Base):
    __tablename__ = "allergens"
    __table_args__ = (UniqueConstraint("code", name="uq_allergen_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128))

class Symptom(Base):
    __tablename__ = "symptoms"
    __table_args__ = (UniqueConstraint("code", name="uq_symptom_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128))

class Medication(Base):
    """
    form: tablet / sl_drops / sl_tablet / injection
    """
    __tablename__ = "medications"
    __table_args__ = (UniqueConstraint("code", name="uq_medication_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128))
    form: Mapped[str] = mapped_column(String(32), index=True)
