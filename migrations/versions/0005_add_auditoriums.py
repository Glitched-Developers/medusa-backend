"""Store the BSU auditorium id to normalized name map."""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auditoriums",
        sa.Column("id", sa.String(length=32), nullable=False, comment="BSU auditorium id"),
        sa.Column("name", sa.String(length=255), nullable=False, comment="Name as published by BSU"),
        sa.Column(
            "token",
            sa.String(length=64),
            nullable=False,
            comment="Normalized room token, e.g. 6-7_12",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="When this row was last seen during a crawl",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auditoriums_token", "auditoriums", ["token"])


def downgrade() -> None:
    op.drop_index("ix_auditoriums_token", table_name="auditoriums")
    op.drop_table("auditoriums")
