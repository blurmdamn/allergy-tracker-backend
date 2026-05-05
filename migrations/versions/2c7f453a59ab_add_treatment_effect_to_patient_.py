"""add treatment effect to patient medications

Revision ID: 2c7f453a59ab
Revises: 407b964a96de
Create Date: 2026-05-05 21:55:00.538522

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c7f453a59ab'
down_revision: Union[str, Sequence[str], None] = '407b964a96de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "patient_medications",
        sa.Column("treatment_effect", sa.String(length=16), nullable=True),
    )

    op.create_check_constraint(
        "ck_patient_medications_treatment_effect",
        "patient_medications",
        "treatment_effect IS NULL OR treatment_effect IN ('good', 'partial', 'none')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_patient_medications_treatment_effect",
        "patient_medications",
        type_="check",
    )

    op.drop_column("patient_medications", "treatment_effect")
