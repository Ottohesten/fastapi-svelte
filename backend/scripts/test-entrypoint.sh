#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "${APP_TEST_DATABASE_GUARD:-}" != "isolated-compose-v1" ]] ||
    [[ "${POSTGRES_SERVER:-}" != "test-db" ]] ||
    [[ "${POSTGRES_DB:-}" != "app_test" ]] ||
    [[ "${POSTGRES_USER:-}" != "test_runner" ]]; then
    echo "Refusing to run database tests outside the isolated Compose environment." >&2
    exit 2
fi

uv run --no-sync python app/backend_pre_start.py
uv run --no-sync alembic upgrade head
exec uv run --no-sync pytest "$@"
