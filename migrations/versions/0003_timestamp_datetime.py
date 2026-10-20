"""Convert schedule timestamps to timezone-aware datetimes."""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("schedule_by_groups") as batch_op:
        batch_op.alter_column("timestamp", existing_type=sa.String(19), type_=sa.DateTime(timezone=True))


def downgrade() -> None:
    with op.batch_alter_table("schedule_by_groups") as batch_op:
        batch_op.alter_column("timestamp", existing_type=sa.DateTime(timezone=True), type_=sa.String(19))
