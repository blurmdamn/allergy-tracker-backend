from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """
    Единая таблица пользователей: пациенты и врачи.
    role: "patient" | "doctor" (в будущем можно "admin")
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    role: Mapped[str] = mapped_column(String(16), default="patient", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DoctorPatient(Base):
    """
    Связь врач↔пациент, чтобы врач видел список своих пациентов.
    Один пациент может быть у нескольких врачей (и наоборот).
    """
    __tablename__ = "doctor_patient"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    doctor_id: Mapped[int] = mapped_column(Integer, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True)

    # Важно: FK ниже как строка — избегает циклических импортов и дружит с Alembic
    # Alembic нормально обработает строковые ForeignKey.
    # (doctor_id/patient_id ссылаются на users.id)
    __mapper_args__ = {"eager_defaults": True}

    # Реальные FK:
    # (SQLAlchemy требует их на колонке, поэтому объявим через ForeignKey строкой)
    from sqlalchemy import ForeignKey  # локальный импорт чтобы не засорять верх
    doctor_id = mapped_column(ForeignKey("users.id"), index=True)
    patient_id = mapped_column(ForeignKey("users.id"), index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
