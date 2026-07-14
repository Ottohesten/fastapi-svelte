from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.config import settings
from app.db import engine, init_db
from app.main import app

from tests.utils.utils import get_superuser_token_headers
from tests.utils.user import authentication_token_from_email


# @pytest.fixture(scope="session", autouse=True)
@pytest.fixture(scope="function", autouse=True)
def db(request: pytest.FixtureRequest) -> Generator[Session | None, None, None]:
    if request.node.get_closest_marker("no_db"):
        yield None
        return

    with Session(engine) as session:
        init_db(session)
        yield session
        # statement = delete(Item)
        # session.execute(statement)
        # statement = delete(User)
        # session.exec(statement)
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
