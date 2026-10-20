"""Allow full schedule timestamps.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("schedule_by_groups") as batch_op:
        batch_op.alter_column(
            "timestamp",
            existing_type=sa.String(length=8),
            type_=sa.String(length=19),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("schedule_by_groups") as batch_op:
        batch_op.alter_column(
            "timestamp",
            existing_type=sa.String(length=19),
            type_=sa.String(length=8),
            existing_nullable=False,
        )
