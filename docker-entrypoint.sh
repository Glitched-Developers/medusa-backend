#!/bin/sh
set -eu

retries="${DB_MIGRATION_RETRIES:-30}"
delay="${DB_MIGRATION_RETRY_DELAY_SECONDS:-2}"
attempt=1
while ! alembic upgrade head; do
    if [ "$attempt" -ge "$retries" ]; then
        echo "Database migrations failed after ${retries} attempts" >&2
        exit 1
    fi
    echo "Database unavailable; retrying migration in ${delay}s (${attempt}/${retries})" >&2
    sleep "$delay"
    attempt=$((attempt + 1))
done
exec uvicorn main:app --host 0.0.0.0 --port "${PORT}"
