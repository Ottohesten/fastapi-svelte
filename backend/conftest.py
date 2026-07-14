from __future__ import annotations

import atexit
import fcntl
import hashlib
import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import IO

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPOSITORY_ROOT / "backend"
COMPOSE_FILES = (
    REPOSITORY_ROOT / "compose.test.yaml",
    REPOSITORY_ROOT / "compose.test.host.yaml",
)

_active_compose_command: tuple[str, ...] | None = None
_test_run_lock: IO[str] | None = None


def _run_command(
    command: tuple[str, ...] | list[str],
    *,
    check: bool = True,
    cwd: Path = REPOSITORY_ROOT,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise pytest.UsageError(
            "Docker Compose is required for database-backed tests. "
            "Install Docker and ensure `docker compose` is available."
        ) from error

    if check and result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise pytest.UsageError(
            f"Could not prepare the isolated test database:\n{details}"
        )
    return result


def _cleanup_test_database() -> None:
    global _active_compose_command, _test_run_lock

    if _active_compose_command is not None:
        result = _run_command(
            [
                *_active_compose_command,
                "down",
                "--volumes",
                "--remove-orphans",
            ],
            check=False,
        )
        if result.returncode != 0:
            details = result.stderr.strip() or result.stdout.strip()
            print(
                f"Warning: could not remove the isolated test database:\n{details}",
                file=sys.stderr,
            )
        _active_compose_command = None

    os.environ.pop("TEST_DB_HOST_PORT", None)
    if _test_run_lock is not None:
        fcntl.flock(_test_run_lock, fcntl.LOCK_UN)
        _test_run_lock.close()
        _test_run_lock = None


def _acquire_test_run_lock(project_name: str) -> None:
    global _test_run_lock

    lock_path = Path(tempfile.gettempdir()) / f"{project_name}.lock"
    lock_file = lock_path.open("w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        lock_file.close()
        raise pytest.UsageError(
            "Another database-backed pytest session is already running for this "
            "checkout. Wait for it to finish before starting another one."
        ) from error
    _test_run_lock = lock_file


def _available_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    if port == 5432:
        return _available_loopback_port()
    return port


def _set_test_environment(*, guard: str, host: str, port: str) -> None:
    test_values = {
        "APP_TEST_DATABASE_GUARD": guard,
        "BACKEND_CORS_ORIGINS": "http://test.invalid",
        "CLOUDINARY_API_KEY": "test-cloudinary-key",
        "CLOUDINARY_API_SECRET": "test-cloudinary-secret",
        "CLOUDINARY_CLOUD_NAME": "test-cloudinary-cloud",
        "EMAIL_TEST_USER": "test-user@example.com",
        "ENVIRONMENT": "local",
        "FIRST_SUPERUSER": "test-admin@example.com",
        "FIRST_SUPERUSER_PASSWORD": "Test-only-password-DO-NOT-USE-123!",
        "FRONTEND_HOST": "http://test.invalid",
        "OPENFOODFACTS_USER_AGENT": "fastapi-svelte-tests/1.0",
        "POSTGRES_DB": "app_test",
        "POSTGRES_PASSWORD": "test_runner_password",
        "POSTGRES_PORT": port,
        "POSTGRES_SERVER": host,
        "POSTGRES_USER": "test_runner",
        "PROJECT_NAME": "FastAPI Svelte Tests",
        "SECRET_KEY": "test-only-secret-key-that-must-never-be-used-elsewhere",
    }
    os.environ.update(test_values)

    # Prevent optional integrations from inheriting real host credentials.
    for variable in (
        "EMAILS_FROM_EMAIL",
        "SENTRY_DSN",
        "SMTP_HOST",
        "SMTP_PASSWORD",
        "SMTP_USER",
    ):
        os.environ.pop(variable, None)


def _migrate_test_database(*, expected_port: int) -> None:
    expected_environment = (
        os.environ.get("APP_TEST_DATABASE_GUARD") == "isolated-pytest-v1"
        and os.environ.get("POSTGRES_SERVER") == "127.0.0.1"
        and os.environ.get("POSTGRES_PORT") == str(expected_port)
        and os.environ.get("POSTGRES_DB") == "app_test"
        and os.environ.get("POSTGRES_USER") == "test_runner"
    )
    if not expected_environment:
        raise pytest.UsageError(
            "Refusing to migrate because pytest did not resolve the exact "
            "isolated database settings."
        )

    _run_command(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
    )


def _uses_only_no_db_tests(config: pytest.Config) -> bool:
    return config.getoption("markexpr").strip() == "no_db"


def pytest_sessionstart(session: pytest.Session) -> None:
    """Prepare an isolated database before pytest imports application test modules."""
    global _active_compose_command

    if os.getenv("APP_TEST_DATABASE_GUARD") == "isolated-compose-v1":
        return

    if session.config.getoption("collectonly") or _uses_only_no_db_tests(
        session.config
    ):
        _set_test_environment(guard="isolated-no-db-v1", host="test-db", port="5432")
        return

    checkout_hash = hashlib.sha256(str(REPOSITORY_ROOT.resolve()).encode()).hexdigest()[
        :12
    ]
    project_name = (
        "fastapi-svelte-vscode-tests-"
        f"{getattr(os, 'getuid', lambda: 0)()}-{checkout_hash}"
    )
    _acquire_test_run_lock(project_name)
    published_port = _available_loopback_port()
    os.environ["TEST_DB_HOST_PORT"] = str(published_port)
    compose_command = (
        "docker",
        "compose",
        "--project-name",
        project_name,
        "--file",
        str(COMPOSE_FILES[0]),
        "--file",
        str(COMPOSE_FILES[1]),
    )

    _active_compose_command = compose_command
    atexit.register(_cleanup_test_database)

    try:
        # Clear a database left by an interrupted Testing panel run.
        _run_command(
            [*compose_command, "down", "--volumes", "--remove-orphans"],
            check=False,
        )
        _run_command([*compose_command, "up", "--detach", "--wait", "test-db"])

        port_result = _run_command([*compose_command, "port", "test-db", "5432"])
        published_addresses = port_result.stdout.strip().splitlines()
        expected_address = f"127.0.0.1:{published_port}"
        if published_addresses != [expected_address]:
            raise pytest.UsageError(
                "Refusing to run database-backed tests because Docker did not "
                "publish the exact requested loopback-only test port."
            )

        _set_test_environment(
            guard="isolated-pytest-v1",
            host="127.0.0.1",
            port=str(published_port),
        )
        _migrate_test_database(expected_port=published_port)
    except BaseException:
        _cleanup_test_database()
        raise


def pytest_sessionfinish() -> None:
    _cleanup_test_database()
