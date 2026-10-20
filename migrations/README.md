# Database migrations

This project uses Alembic with SQLAlchemy and SQLite.

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration after changing the schema
alembic revision -m "describe the schema change"

# Roll back the latest migration
alembic downgrade -1
```

The database URL is configured in `alembic.ini`. Override it without editing
the file by setting `DATABASE_URL` to a SQLAlchemy URL.
