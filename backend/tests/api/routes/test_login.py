from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

import app.db_crud as db_crud
import app.security as security
from app.config import settings
from app.models import User, UserCreate
from tests.utils.utils import random_email, random_lower_string


@dataclass(frozen=True)
class UserCredentials:
    user: User
    password: str


UserFactory = Callable[..., UserCredentials]


@pytest.fixture
def user_factory(db: Session) -> UserFactory:
    """Create users inside the function-scoped rollback transaction."""

    def create_user(
        *,
        is_active: bool = True,
        custom_scopes: list[str] | None = None,
    ) -> UserCredentials:
        password = random_lower_string()
        user = db_crud.create_user(
            session=db,
            user_create=UserCreate(
                email=random_email(),
                password=password,
                is_active=is_active,
            ),
        )
        if custom_scopes:
            # Reassignment is intentional so SQLAlchemy records the JSON change.
            user.custom_scopes = list(custom_scopes)
            db.add(user)
            db.commit()
            db.refresh(user)
        return UserCredentials(user=user, password=password)

    return create_user


def _login(client: TestClient, credentials: UserCredentials) -> dict[str, str]:
    response = client.post(
        "/login/access-token",
        data={
            "username": credentials.user.email,
            "password": credentials.password,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["access_token"], str)
    assert isinstance(payload["refresh_token"], str)
    return payload


def _claims(token: str) -> dict[str, object]:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[security.ALGORITHM],
    )


def test_login_returns_access_and_persisted_refresh_tokens(
    client: TestClient,
    db: Session,
    user_factory: UserFactory,
) -> None:
    credentials = user_factory(custom_scopes=["recipes:create"])

    tokens = _login(client, credentials)

    access_claims = _claims(tokens["access_token"])
    assert access_claims["sub"] == credentials.user.email
    assert access_claims["type"] == "access"
    assert access_claims["scopes"] == ["recipes:create"]

    refresh_claims = _claims(tokens["refresh_token"])
    assert refresh_claims["sub"] == credentials.user.email
    assert refresh_claims["type"] == "refresh"
    assert (
        db_crud.get_refresh_token(session=db, token=tokens["refresh_token"]) is not None
    )
    assert client.cookies.get("refresh_token") == tokens["refresh_token"]


@pytest.mark.parametrize("unknown_user", [False, True])
def test_login_rejects_invalid_credentials(
    client: TestClient,
    user_factory: UserFactory,
    unknown_user: bool,
) -> None:
    credentials = user_factory()
    email = random_email() if unknown_user else credentials.user.email

    response = client.post(
        "/login/access-token",
        data={"username": email, "password": random_lower_string()},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect email or password"}


def test_login_rejects_inactive_user(
    client: TestClient,
    user_factory: UserFactory,
) -> None:
    credentials = user_factory(is_active=False)

    response = client.post(
        "/login/access-token",
        data={
            "username": credentials.user.email,
            "password": credentials.password,
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Inactive user"}


def test_token_endpoint_returns_authenticated_user(
    client: TestClient,
    user_factory: UserFactory,
) -> None:
    credentials = user_factory()
    tokens = _login(client, credentials)

    response = client.post(
        "/login/test-token",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(credentials.user.id)
    assert response.json()["email"] == credentials.user.email


def test_token_endpoint_requires_bearer_token(client: TestClient) -> None:
    response = client.post("/login/test-token")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_refresh_token_cannot_be_used_as_access_token(
    client: TestClient,
    user_factory: UserFactory,
) -> None:
    credentials = user_factory()
    tokens = _login(client, credentials)
    headers = {"Authorization": f"Bearer {tokens['refresh_token']}"}

    required_auth_response = client.post("/login/test-token", headers=headers)
    optional_auth_response = client.get("/recipes/", headers=headers)

    assert required_auth_response.status_code == 401
    assert required_auth_response.json() == {"detail": "Could not validate credentials"}
    assert optional_auth_response.status_code == 401
    assert optional_auth_response.json() == {"detail": "Could not validate credentials"}


def test_access_token_for_unknown_user_is_rejected(client: TestClient) -> None:
    token = security.create_access_token(
        data={"sub": random_email(), "scopes": []},
        expires_delta=timedelta(minutes=5),
    )

    response = client.post(
        "/login/test-token",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_refresh_rotates_token_and_rejects_reuse(
    client: TestClient,
    db: Session,
    user_factory: UserFactory,
) -> None:
    credentials = user_factory()
    original = _login(client, credentials)["refresh_token"]

    response = client.post("/login/refresh", json={"refresh_token": original})

    assert response.status_code == 200
    rotated = response.json()
    assert rotated["refresh_token"] != original
    assert _claims(rotated["access_token"])["type"] == "access"
    assert _claims(rotated["refresh_token"])["type"] == "refresh"

    original_record = db_crud.get_refresh_token(session=db, token=original)
    rotated_record = db_crud.get_refresh_token(
        session=db, token=rotated["refresh_token"]
    )
    assert original_record is not None
    assert original_record.revoked_at is not None
    assert rotated_record is not None
    assert rotated_record.revoked_at is None

    reused = client.post("/login/refresh", json={"refresh_token": original})
    assert reused.status_code == 401
    assert reused.json() == {"detail": "Refresh token revoked"}


def test_refresh_rejects_revoked_token(
    client: TestClient,
    db: Session,
    user_factory: UserFactory,
) -> None:
    credentials = user_factory()
    refresh_token = _login(client, credentials)["refresh_token"]
    db_crud.revoke_refresh_token(session=db, token=refresh_token)

    response = client.post("/login/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 401
    assert response.json() == {"detail": "Refresh token revoked"}


def test_refresh_rejects_database_expired_token(
    client: TestClient,
    db: Session,
    user_factory: UserFactory,
) -> None:
    credentials = user_factory()
    refresh_token = _login(client, credentials)["refresh_token"]
    record = db_crud.get_refresh_token(session=db, token=refresh_token)
    assert record is not None
    record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.add(record)
    db.commit()

    response = client.post("/login/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 401
    assert response.json() == {"detail": "Refresh token expired"}


def test_refresh_rejects_access_token(
    client: TestClient,
    user_factory: UserFactory,
) -> None:
    credentials = user_factory()
    access_token = _login(client, credentials)["access_token"]

    response = client.post("/login/refresh", json={"refresh_token": access_token})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token type"}


def test_refresh_rejects_user_deactivated_after_login(
    client: TestClient,
    db: Session,
    user_factory: UserFactory,
) -> None:
    credentials = user_factory()
    refresh_token = _login(client, credentials)["refresh_token"]
    credentials.user.is_active = False
    db.add(credentials.user)
    db.commit()

    response = client.post("/login/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid user"}


def test_logout_revokes_refresh_token_and_clears_cookie(
    client: TestClient,
    db: Session,
    user_factory: UserFactory,
) -> None:
    credentials = user_factory()
    refresh_token = _login(client, credentials)["refresh_token"]
    assert client.cookies.get("refresh_token") == refresh_token

    response = client.post("/logout", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out"}
    assert client.cookies.get("refresh_token") is None
    record = db_crud.get_refresh_token(session=db, token=refresh_token)
    assert record is not None
    assert record.revoked_at is not None

    refresh_response = client.post(
        "/login/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 401
    assert refresh_response.json() == {"detail": "Refresh token revoked"}
