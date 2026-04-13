from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CheckinQuestion(Base):
    __tablename__ = "checkin_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    text: Mapped[str] = mapped_column(Text)

    # nasal | ocular | wellbeing | activity | sleep | trigger | medication | note
    domain: Mapped[str] = mapped_column(String(50), index=True)

    # scale_0_3 | boolean | single_choice | multi_choice | text
    answer_type: Mapped[str] = mapped_column(String(50))

    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DailyCheckin(Base):
    __tablename__ = "daily_checkins"
    __table_args__ = (
        UniqueConstraint("user_id", "checkin_date", name="uq_daily_checkins_user_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    checkin_date: Mapped[date] = mapped_column(Date, index=True)

    # агрегаты симптомов
    nasal_score: Mapped[int] = mapped_column(Integer, default=0)
    ocular_score: Mapped[int] = mapped_column(Integer, default=0)
    symptom_total_score: Mapped[int] = mapped_column(Integer, default=0)

    # лекарства и общий дневной итог
    medication_score: Mapped[int] = mapped_column(Integer, default=0)
    day_total_score: Mapped[int] = mapped_column(Integer, default=0)

    # none | mild | moderate | high | severe
    severity_level: Mapped[str] = mapped_column(String(20), default="none", index=True)

    # дополнительные показатели
    wellbeing_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    activity_impact_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sleep_impact_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    had_allergen_contact: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    trigger_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class DailyCheckinAnswer(Base):
    __tablename__ = "daily_checkin_answers"
    __table_args__ = (
        UniqueConstraint("checkin_id", "question_id", name="uq_checkin_answer_question"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    checkin_id: Mapped[int] = mapped_column(ForeignKey("daily_checkins.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("checkin_questions.id"), index=True)

    # одно из полей используется в зависимости от типа вопроса
    score_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bool_value: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    text_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    choice_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    choice_values_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class DailyMedicationUsage(Base):
    __tablename__ = "daily_medication_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    checkin_id: Mapped[int] = mapped_column(ForeignKey("daily_checkins.id", ondelete="CASCADE"), index=True)
    patient_medication_id: Mapped[int] = mapped_column(ForeignKey("patient_medications.id"), index=True)

    times_taken: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # good | partial | none
    effect: Mapped[str | None] = mapped_column(String(20), nullable=True)

    note: Mapped[str | None] = mapped_column(Text, nullable=True)