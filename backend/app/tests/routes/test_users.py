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


def test_get_users_normal_user_me(client: TestClient, normal_user_token_headers: dict[str, str]):
    """
    Test the /users/me endpoint for normal user
    """
    r = client.get(f"/users/me", headers=normal_user_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is False
    assert current_user["email"] == settings.EMAIL_TEST_USER


# def test_create_user_new_email(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
#     with (
#         patch("app.utils.send_email", return_value=None),
#         patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
#         patch("app.core.config.settings.SMTP_USER", "admin@example.com"),
#     ):
#         username = random_email()
#         password = random_lower_string()
#         data = {"email": username, "password": password}
#         r = client.post(
#             f"/users/",
#             headers=superuser_token_headers,
#             json=data,
#         )
#         assert 200 <= r.status_code < 300
#         created_user = r.json()
#         user = db_crud.get_user_by_email(session=db, email=username)
#         assert user
#         assert user.email == created_user["email"]


def test_get_existing_user_superuser(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/{user_id} endpoint for superuser
    """
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = db_crud.create_user(session=db, user_create=user_in)
    user_id = user.id

    r = client.get(f"/users/{user_id}", headers=superuser_token_headers)

    assert 200 <= r.status_code < 300
    api_user = r.json()
    existing_user = db_crud.get_user_by_email(session=db, email=username)
    assert existing_user
    assert existing_user.email == api_user["email"]


def test_get_existing_user_permissions_error(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    """
    Test the /users/{user_id} endpoint for normal user

    Should return 403 forbidden error
    """
    r = client.get(
        f"/users/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "The user doesn't have enough privileges"}