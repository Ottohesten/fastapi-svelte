"""
The purpose of this file is to provide fixtures for testing the FastAPI application.
"""


from collections.abc import Generator
import os
import subprocess

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete, StaticPool, SQLModel, create_engine

from app.config import settings
from app.db import engine, init_db
from app.main import app
from app.models import User

from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers




# @pytest.fixture(scope="session", autouse=True)
@pytest.fixture(scope="function", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        # statement = delete(Item)
        # session.execute(statement)
        # statement = delete(User)
        # session.execute(statement)
        # session.commit()


# @pytest.fixture(scope="module")
@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c



# @pytest.fixture(scope="module")
@pytest.fixture(scope="function")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


# @pytest.fixture(scope="module")
@pytest.fixture(scope="function")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


@pytest.fixture(autouse=True, scope="function")
# @pytest.fixture(autouse=True, scope="session")
def clean_db(db):
    yield
    # After each test, delete all data from all tables
    for table in reversed(SQLModel.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()


@pytest.fixture(scope="session", autouse=True)
def set_testing_env():
    print("Setting TESTING environment variable to 1")
    # Set TESTING=1 before tests
    os.environ["TESTING"] = "1"
    yield
    # Reset TESTING to 0 after tests
    print("Resetting TESTING environment variable to 0")
    os.environ["TESTING"] = "0"