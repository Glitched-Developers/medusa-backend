"""SQLAlchemy Core tables for mail accounts and push devices."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Table, Text

from database import meta

user_mail_accounts = Table(
    "user_mail_accounts", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String(64), nullable=False, unique=True, index=True),
    Column("email", String(128), nullable=False),
    Column("password_encrypted", Text, nullable=False),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
)

user_devices = Table(
    "user_devices", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String(64), ForeignKey("user_mail_accounts.user_id", ondelete="CASCADE"), nullable=False),
    Column("fcm_token", String(255), nullable=False, unique=True),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
    Index("ix_user_devices_user_id", "user_id"),
)
