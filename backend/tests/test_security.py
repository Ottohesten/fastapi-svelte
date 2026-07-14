from datetime import timedelta

import jwt
import pytest

from app.config import settings
from app.db_crud import hash_token
from app.security import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)


pytestmark = pytest.mark.no_db


def _decode(token: str) -> dict[str, object]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def test_create_access_token_adds_access_type_without_mutating_input() -> None:
    claims = {"sub": "person@example.com", "scopes": ["recipes:read"]}

    token = create_access_token(claims, expires_delta=timedelta(minutes=5))

    decoded = _decode(token)
    assert decoded["sub"] == claims["sub"]
    assert decoded["scopes"] == claims["scopes"]
    assert decoded["type"] == "access"
    assert "exp" in decoded
    assert claims == {"sub": "person@example.com", "scopes": ["recipes:read"]}


def test_create_refresh_token_adds_refresh_type() -> None:
    token = create_refresh_token(
        {"sub": "person@example.com"}, expires_delta=timedelta(days=1)
    )

    decoded = _decode(token)
    assert decoded["sub"] == "person@example.com"
    assert decoded["type"] == "refresh"
    assert isinstance(decoded["jti"], str)


def test_refresh_tokens_are_unique_even_when_created_immediately() -> None:
    claims = {"sub": "person@example.com"}

    first = create_refresh_token(claims, expires_delta=timedelta(days=1))
    second = create_refresh_token(claims, expires_delta=timedelta(days=1))

    assert first != second
    assert _decode(first)["jti"] != _decode(second)["jti"]


def test_expired_token_is_rejected_by_jwt_validation() -> None:
    token = create_access_token(
        {"sub": "person@example.com", "scopes": []},
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        _decode(token)


def test_password_hash_verification() -> None:
    password = "correct horse battery staple"

    hashed_password = get_password_hash(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password)
    assert not verify_password("incorrect password", hashed_password)


def test_refresh_token_hash_is_deterministic_and_non_reversible() -> None:
    token = "sensitive-refresh-token"

    hashed_token = hash_token(token)

    assert hashed_token == hash_token(token)
    assert hashed_token != token
    assert len(hashed_token) == 64
