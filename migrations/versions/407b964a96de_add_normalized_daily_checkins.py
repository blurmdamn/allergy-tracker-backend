"""add normalized daily checkins

Revision ID: 407b964a96de
Revises: ff8e94b2ffb8
Create Date: 2026-04-14 01:14:57.893481

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "407b964a96de"
down_revision: Union[str, Sequence[str], None] = "ff8e94b2ffb8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "checkin_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(length=50), nullable=False),
        sa.Column("answer_type", sa.String(length=50), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_checkin_questions_code"),
    )
    op.create_index("ix_checkin_questions_code", "checkin_questions", ["code"], unique=False)
    op.create_index("ix_checkin_questions_domain", "checkin_questions", ["domain"], unique=False)

    op.create_table(
        "daily_checkins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("checkin_date", sa.Date(), nullable=False),
        sa.Column("nasal_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ocular_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("symptom_total_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("medication_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("day_total_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("severity_level", sa.String(length=20), nullable=False, server_default="none"),
        sa.Column("wellbeing_score", sa.Integer(), nullable=True),
        sa.Column("activity_impact_score", sa.Integer(), nullable=True),
        sa.Column("sleep_impact_score", sa.Integer(), nullable=True),
        sa.Column("had_allergen_contact", sa.Boolean(), nullable=True),
        sa.Column("trigger_note", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "checkin_date", name="uq_daily_checkins_user_date"),
    )
    op.create_index("ix_daily_checkins_user_id", "daily_checkins", ["user_id"], unique=False)
    op.create_index("ix_daily_checkins_checkin_date", "daily_checkins", ["checkin_date"], unique=False)
    op.create_index("ix_daily_checkins_severity_level", "daily_checkins", ["severity_level"], unique=False)

    op.create_table(
        "daily_checkin_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("checkin_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("score_value", sa.Integer(), nullable=True),
        sa.Column("bool_value", sa.Boolean(), nullable=True),
        sa.Column("text_value", sa.Text(), nullable=True),
        sa.Column("choice_value", sa.String(length=100), nullable=True),
        sa.Column("choice_values_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["checkin_id"], ["daily_checkins.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["checkin_questions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("checkin_id", "question_id", name="uq_checkin_answer_question"),
    )
    op.create_index("ix_daily_checkin_answers_checkin_id", "daily_checkin_answers", ["checkin_id"], unique=False)
    op.create_index("ix_daily_checkin_answers_question_id", "daily_checkin_answers", ["question_id"], unique=False)

    op.create_table(
        "daily_medication_usage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("checkin_id", sa.Integer(), nullable=False),
        sa.Column("patient_medication_id", sa.Integer(), nullable=False),
        sa.Column("times_taken", sa.Integer(), nullable=True),
        sa.Column("effect", sa.String(length=20), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["checkin_id"], ["daily_checkins.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_medication_id"], ["patient_medications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_daily_medication_usage_checkin_id", "daily_medication_usage", ["checkin_id"], unique=False)
    op.create_index("ix_daily_medication_usage_patient_medication_id", "daily_medication_usage", ["patient_medication_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_daily_medication_usage_patient_medication_id", table_name="daily_medication_usage")
    op.drop_index("ix_daily_medication_usage_checkin_id", table_name="daily_medication_usage")
    op.drop_table("daily_medication_usage")

    op.drop_index("ix_daily_checkin_answers_question_id", table_name="daily_checkin_answers")
    op.drop_index("ix_daily_checkin_answers_checkin_id", table_name="daily_checkin_answers")
    op.drop_table("daily_checkin_answers")

    op.drop_index("ix_daily_checkins_severity_level", table_name="daily_checkins")
    op.drop_index("ix_daily_checkins_checkin_date", table_name="daily_checkins")
    op.drop_index("ix_daily_checkins_user_id", table_name="daily_checkins")
    op.drop_table("daily_checkins")

    op.drop_index("ix_checkin_questions_domain", table_name="checkin_questions")
    op.drop_index("ix_checkin_questions_code", table_name="checkin_questions")
    op.drop_table("checkin_questions")