from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """
    Основной пользователь системы.
    Сейчас приложение ориентировано на personal tracker,
    поэтому публичная регистрация разрешает только роль patient.
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
    Историческая таблица из более ранней версии идеи проекта.
    Сейчас в API не используется, но остаётся в модели,
    чтобы не ломать уже существующую миграцию.
    """
    __tablename__ = "doctor_patient"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)