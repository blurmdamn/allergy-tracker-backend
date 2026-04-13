"""init tables

Revision ID: ff8e94b2ffb8
Revises:
Create Date: 2026-01-10 04:27:37.493759

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ff8e94b2ffb8"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ROLE_VALUES = ("patient",)
SEX_VALUES = ("female", "male", "other")
FREQUENCY_VALUES = ("contact_only", "daily")
REGIMEN_VALUES = ("conventional", "daily", "accelerated")
REMINDER_TYPE_VALUES = ("asit_visit", "daily_checkin", "questionnaire", "custom")
ASIT_STATUS_VALUES = ("planned", "done", "skipped", "rescheduled")
EFFECT_VALUES = ("good", "partial", "none")


def _in(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def upgrade() -> None:
    op.create_table(
        "allergens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_allergen_code"),
    )
    op.create_index(op.f("ix_allergens_code"), "allergens", ["code"], unique=False)

    op.create_table(
        "medications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("form", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_medication_code"),
    )
    op.create_index(op.f("ix_medications_code"), "medications", ["code"], unique=False)
    op.create_index(op.f("ix_medications_form"), "medications", ["form"], unique=False)

    op.create_table(
        "symptoms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_symptom_code"),
    )
    op.create_index(op.f("ix_symptoms_code"), "symptoms", ["code"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(f"role IN ({_in(ROLE_VALUES)})", name="ck_users_role"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.create_table(
        "asit_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("regimen", sa.String(length=32), nullable=False),
        sa.Column("target_allergen_id", sa.Integer(), nullable=True),
        sa.Column("medication_id", sa.Integer(), nullable=True),
        sa.Column("interval_days", sa.Integer(), nullable=True),
        sa.Column("dose_unit", sa.String(length=32), nullable=True),
        sa.Column("started_at", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(f"regimen IN ({_in(REGIMEN_VALUES)})", name="ck_asit_plans_regimen"),
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"]),
        sa.ForeignKeyConstraint(["target_allergen_id"], ["allergens.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_asit_plans_user_id"), "asit_plans", ["user_id"], unique=False)

    op.create_table(
        "patient_allergen",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("allergen_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["allergen_id"], ["allergens.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id", "allergen_id"),
    )

    op.create_table(
        "patient_allergy",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("symptoms_start_date", sa.Date(), nullable=True),
        sa.Column("frequency", sa.String(length=32), nullable=True),
        sa.CheckConstraint(
            f"frequency IS NULL OR frequency IN ({_in(FREQUENCY_VALUES)})",
            name="ck_patient_allergy_frequency",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "patient_allergy_months",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("month_no", sa.Integer(), nullable=False),
        sa.CheckConstraint("month_no BETWEEN 1 AND 12", name="ck_patient_allergy_months_month_no"),
        sa.ForeignKeyConstraint(["user_id"], ["patient_allergy.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "month_no"),
    )

    op.create_table(
        "patient_medications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("medication_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.Date(), nullable=True),
        sa.Column("ended_at", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("dose_text", sa.String(length=64), nullable=True),
        sa.Column("times_per_day", sa.Integer(), nullable=True),
        sa.Column("interval_hours", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_patient_medications_medication_id"), "patient_medications", ["medication_id"], unique=False)
    op.create_index(op.f("ix_patient_medications_user_id"), "patient_medications", ["user_id"], unique=False)

    op.create_table(
        "patient_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("sex", sa.String(length=16), nullable=True),
        sa.CheckConstraint(
            f"sex IS NULL OR sex IN ({_in(SEX_VALUES)})",
            name="ck_patient_profiles_sex",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "patient_symptom",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("symptom_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["symptom_id"], ["symptoms.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id", "symptom_id"),
    )

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("message", sa.String(length=512), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("active_months", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(f"type IN ({_in(REMINDER_TYPE_VALUES)})", name="ck_reminders_type"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reminders_scheduled_at"), "reminders", ["scheduled_at"], unique=False)
    op.create_index(op.f("ix_reminders_user_id"), "reminders", ["user_id"], unique=False)

    op.create_table(
        "asit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("planned_date", sa.Date(), nullable=False),
        sa.Column("actual_date", sa.Date(), nullable=True),
        sa.Column("dose_value", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("note", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(f"status IN ({_in(ASIT_STATUS_VALUES)})", name="ck_asit_events_status"),
        sa.ForeignKeyConstraint(["plan_id"], ["asit_plans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_asit_events_plan_id"), "asit_events", ["plan_id"], unique=False)
    op.create_index(op.f("ix_asit_events_planned_date"), "asit_events", ["planned_date"], unique=False)

    op.create_table(
        "medication_intake_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_medication_id", sa.Integer(), nullable=False),
        sa.Column("logged_at", sa.DateTime(), nullable=False),
        sa.Column("dose_taken", sa.Integer(), nullable=True),
        sa.Column("effect", sa.String(length=16), nullable=True),
        sa.Column("note", sa.String(length=512), nullable=True),
        sa.CheckConstraint(
            f"effect IS NULL OR effect IN ({_in(EFFECT_VALUES)})",
            name="ck_medication_intake_logs_effect",
        ),
        sa.ForeignKeyConstraint(["patient_medication_id"], ["patient_medications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_medication_intake_logs_patient_medication_id"),
        "medication_intake_logs",
        ["patient_medication_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_medication_intake_logs_patient_medication_id"), table_name="medication_intake_logs")
    op.drop_table("medication_intake_logs")
    op.drop_index(op.f("ix_asit_events_planned_date"), table_name="asit_events")
    op.drop_index(op.f("ix_asit_events_plan_id"), table_name="asit_events")
    op.drop_table("asit_events")
    op.drop_index(op.f("ix_reminders_user_id"), table_name="reminders")
    op.drop_index(op.f("ix_reminders_scheduled_at"), table_name="reminders")
    op.drop_table("reminders")
    op.drop_table("patient_symptom")
    op.drop_table("patient_profiles")
    op.drop_index(op.f("ix_patient_medications_user_id"), table_name="patient_medications")
    op.drop_index(op.f("ix_patient_medications_medication_id"), table_name="patient_medications")
    op.drop_table("patient_medications")
    op.drop_table("patient_allergy_months")
    op.drop_table("patient_allergy")
    op.drop_table("patient_allergen")
    op.drop_index(op.f("ix_asit_plans_user_id"), table_name="asit_plans")
    op.drop_table("asit_plans")
    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_symptoms_code"), table_name="symptoms")
    op.drop_table("symptoms")
    op.drop_index(op.f("ix_medications_form"), table_name="medications")
    op.drop_index(op.f("ix_medications_code"), table_name="medications")
    op.drop_table("medications")
    op.drop_index(op.f("ix_allergens_code"), table_name="allergens")
    op.drop_table("allergens")
