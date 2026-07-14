from __future__ import annotations

from collections.abc import Callable

import pytest
from sqlmodel import Session

import app.db_crud as db_crud
from app.models import Role, User, UserCreate
from app.permissions import (
    AVAILABLE_SCOPES,
    ROLE_TEMPLATES,
    assign_role_to_user,
    create_role_from_template,
    get_user_effective_scopes,
    grant_custom_scope_to_user,
    remove_role_from_user,
    revoke_custom_scope_from_user,
    user_has_all_scopes,
    user_has_any_scope,
    user_has_scope,
)
from tests.utils.utils import random_email, random_lower_string


def _detached_user(
    *,
    roles: list[Role] | None = None,
    custom_scopes: list[str] | None = None,
    is_superuser: bool = False,
) -> User:
    user = User(
        email=random_email(),
        hashed_password="not-used",
        is_superuser=is_superuser,
    )
    user.roles = list(roles or [])
    user.custom_scopes = list(custom_scopes or [])
    return user


@pytest.mark.no_db
class TestPermissionEvaluation:
    def test_effective_scopes_union_roles_and_custom_grants(self) -> None:
        user = _detached_user(
            roles=[
                Role(
                    name="Contributor",
                    scopes=["recipes:read", "ingredients:read"],
                ),
                Role(
                    name="Editor",
                    scopes=["recipes:read", "recipes:update"],
                ),
            ],
            custom_scopes=["recipes:update", "recipes:create"],
        )

        assert get_user_effective_scopes(user) == {
            "ingredients:read",
            "recipes:create",
            "recipes:read",
            "recipes:update",
        }

    def test_superuser_receives_copy_of_every_available_scope(self) -> None:
        user = _detached_user(is_superuser=True)

        effective_scopes = get_user_effective_scopes(user)

        assert effective_scopes == AVAILABLE_SCOPES
        effective_scopes.remove("recipes:read")
        assert "recipes:read" in AVAILABLE_SCOPES

    def test_scope_predicates_cover_positive_and_negative_cases(self) -> None:
        user = _detached_user(custom_scopes=["recipes:read", "recipes:update"])

        assert user_has_scope(user, "recipes:read")
        assert not user_has_scope(user, "recipes:delete")
        assert user_has_any_scope(user, ["recipes:delete", "recipes:update"])
        assert not user_has_any_scope(user, ["recipes:delete", "games:update"])
        assert user_has_all_scopes(user, ["recipes:read", "recipes:update"])
        assert not user_has_all_scopes(user, ["recipes:read", "recipes:delete"])
        assert not user_has_any_scope(user, [])
        assert user_has_all_scopes(user, [])

    def test_superuser_passes_all_scope_predicates(self) -> None:
        user = _detached_user(is_superuser=True)

        assert user_has_scope(user, "not-a-real-scope")
        assert user_has_any_scope(user, ["not-a-real-scope"])
        assert user_has_all_scopes(user, ["not-a-real-scope"])


UserFactory = Callable[[], User]
RoleFactory = Callable[..., Role]


@pytest.fixture
def permission_user_factory(db: Session) -> UserFactory:
    def create_user() -> User:
        return db_crud.create_user(
            session=db,
            user_create=UserCreate(
                email=random_email(),
                password=random_lower_string(),
            ),
        )

    return create_user


@pytest.fixture
def role_factory(db: Session) -> RoleFactory:
    def create_role(
        *, name: str | None = None, scopes: list[str] | None = None
    ) -> Role:
        role = Role(
            name=name or random_lower_string(),
            scopes=list(scopes or []),
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    return create_role


def test_assign_and_remove_role_are_idempotent(
    db: Session,
    permission_user_factory: UserFactory,
    role_factory: RoleFactory,
) -> None:
    user = permission_user_factory()
    role = role_factory(scopes=["recipes:read"])

    assert assign_role_to_user(db, user, role.name)
    assert assign_role_to_user(db, user, role.name)
    db.expire_all()
    stored_user = db.get(User, user.id)
    assert stored_user is not None
    assert [stored_role.id for stored_role in stored_user.roles] == [role.id]

    assert remove_role_from_user(db, stored_user, role.name)
    assert remove_role_from_user(db, stored_user, role.name)
    db.expire_all()
    stored_user = db.get(User, user.id)
    assert stored_user is not None
    assert stored_user.roles == []


def test_assign_and_remove_missing_role_return_false(
    db: Session,
    permission_user_factory: UserFactory,
) -> None:
    user = permission_user_factory()

    assert not assign_role_to_user(db, user, "missing-role")
    assert not remove_role_from_user(db, user, "missing-role")


def test_grant_and_revoke_custom_scope_are_idempotent(
    db: Session,
    permission_user_factory: UserFactory,
) -> None:
    user = permission_user_factory()

    assert grant_custom_scope_to_user(db, user, "recipes:create")
    assert grant_custom_scope_to_user(db, user, "recipes:create")
    db.expire_all()
    stored_user = db.get(User, user.id)
    assert stored_user is not None
    assert stored_user.custom_scopes == ["recipes:create"]

    assert revoke_custom_scope_from_user(db, stored_user, "recipes:create")
    assert revoke_custom_scope_from_user(db, stored_user, "recipes:create")
    db.expire_all()
    stored_user = db.get(User, user.id)
    assert stored_user is not None
    assert stored_user.custom_scopes == []


def test_grant_rejects_unknown_scope_without_mutating_user(
    db: Session,
    permission_user_factory: UserFactory,
) -> None:
    user = permission_user_factory()

    assert not grant_custom_scope_to_user(db, user, "unknown:scope")
    db.refresh(user)
    assert user.custom_scopes == []


def test_create_role_from_template_is_idempotent(db: Session) -> None:
    created = create_role_from_template(db, "viewer")
    created.description = "stale description"
    created.scopes = []
    db.add(created)
    db.commit()

    updated = create_role_from_template(db, "viewer")

    assert updated.id == created.id
    assert updated.name == ROLE_TEMPLATES["viewer"]["name"]
    assert updated.description == ROLE_TEMPLATES["viewer"]["description"]
    assert updated.scopes == ROLE_TEMPLATES["viewer"]["scopes"]


def test_create_role_from_unknown_template_fails(db: Session) -> None:
    with pytest.raises(ValueError, match="Unknown role template"):
        create_role_from_template(db, "missing-template")
