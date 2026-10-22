"""Add mail accounts and push devices."""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_mail_accounts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("email", sa.String(128), nullable=False),
        sa.Column("password_encrypted", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_mail_accounts_user_id", "user_mail_accounts", ["user_id"], unique=True)
    op.create_table(
        "user_devices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("user_mail_accounts.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("fcm_token", sa.String(255), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("fcm_token"),
    )
    op.create_index("ix_user_devices_user_id", "user_devices", ["user_id"])
    op.create_index("ix_user_devices_fcm_token", "user_devices", ["fcm_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_devices_fcm_token", table_name="user_devices")
    op.drop_index("ix_user_devices_user_id", table_name="user_devices")
    op.drop_table("user_devices")
    op.drop_index("ix_user_mail_accounts_user_id", table_name="user_mail_accounts")
    op.drop_table("user_mail_accounts")
