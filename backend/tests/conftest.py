from __future__ import annotations

import os
from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlmodel import Session


def assert_isolated_test_database() -> None:
    from app.config import settings

    compose_database = (
        os.getenv("APP_TEST_DATABASE_GUARD") == "isolated-compose-v1"
        and settings.POSTGRES_SERVER == "test-db"
        and settings.POSTGRES_PORT == 5432
    )
    pytest_database = (
        os.getenv("APP_TEST_DATABASE_GUARD") == "isolated-pytest-v1"
        and settings.POSTGRES_SERVER == "127.0.0.1"
        and settings.POSTGRES_PORT != 5432
    )
    isolated_database = (
        (compose_database or pytest_database)
        and settings.POSTGRES_DB == "app_test"
        and settings.POSTGRES_USER == "test_runner"
    )
    if not isolated_database:
        pytest.fail(
            "Refusing to connect database-backed tests to a non-isolated database. "
            "Run pytest normally and allow it to start the test database."
        )


def reset_test_database() -> None:
    from sqlmodel import SQLModel

    from app.db import engine

    quoted_tables = [
        engine.dialect.identifier_preparer.quote(table.name)
        for table in SQLModel.metadata.sorted_tables
    ]
    if not quoted_tables:
        return

    with engine.begin() as connection:
        connection.exec_driver_sql(
            f"TRUNCATE TABLE {', '.join(quoted_tables)} RESTART IDENTITY CASCADE"
        )


@pytest.fixture(scope="session")
def prepared_database() -> Generator[None, None, None]:
    """Create one clean, seeded baseline for the entire test session."""
    from sqlmodel import Session

    from app.db import engine, init_db

    assert_isolated_test_database()
    reset_test_database()

    with Session(engine) as session:
        init_db(session)

    yield


@pytest.fixture(scope="function", autouse=True)
def db(request: pytest.FixtureRequest) -> Generator[Session | None, None, None]:
    """Give each database test a transaction and roll it back afterwards."""
    if request.node.get_closest_marker("no_db"):
        yield None
        return

    # Resolve lazily so `pytest -m no_db` never prepares or connects to a database.
    request.getfixturevalue("prepared_database")

    from sqlmodel import Session

    from app.db import engine
    from app.deps import get_db
    from app.main import app

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    def override_get_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture(scope="session")
def session_client() -> Generator[TestClient, None, None]:
    """Reuse the application client while keeping per-test cookie state separate."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def client(session_client: TestClient) -> Generator[TestClient, None, None]:
    session_client.cookies.clear()
    try:
        yield session_client
    finally:
        session_client.cookies.clear()


@pytest.fixture(scope="module")
def superuser_token_headers(
    session_client: TestClient, prepared_database: None
) -> dict[str, str]:
    from tests.utils.utils import get_superuser_token_headers

    headers = get_superuser_token_headers(session_client)
    session_client.cookies.clear()
    return headers


@pytest.fixture(scope="module")
def normal_user_token_headers(
    session_client: TestClient, prepared_database: None
) -> dict[str, str]:
    from sqlmodel import Session

    from app.config import settings
    from app.db import engine
    from tests.utils.user import authentication_token_from_email

    with Session(engine) as session:
        headers = authentication_token_from_email(
            client=session_client,
            email=settings.EMAIL_TEST_USER,
            db=session,
        )
    session_client.cookies.clear()
    return headers
