"""Create the schedule storage table.

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None


def upgrade() -> None:
    op.create_table(
        "schedule_by_groups",
        sa.Column("group", sa.Integer(), nullable=False, comment="BSU group ID"),
        sa.Column("data", sa.String(), nullable=False, comment="JSON schedule data"),
        sa.Column(
            "timestamp",
            sa.String(length=8),
            nullable=False,
            comment="Last update timestamp",
        ),
        sa.PrimaryKeyConstraint("group"),
    )


def downgrade() -> None:
    op.drop_table("schedule_by_groups")
