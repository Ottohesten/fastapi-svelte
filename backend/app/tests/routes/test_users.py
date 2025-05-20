import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import db_crud
from app.config import settings
from app.security import verify_password
from app.models import (
    User,
    UserCreate
)
from app.tests.utils.utils import (
    random_email,
    random_lower_string,
)


def test_get_users_superuser_me(client: TestClient, superuser_token_headers: dict[str, str]):
    """
    Test the /users/me endpoint for superuser
    """
    r = client.get(f"/users/me", headers=superuser_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"]
    assert current_user["email"] == settings.FIRST_SUPERUSER
