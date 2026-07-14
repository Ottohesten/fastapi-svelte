import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import db_crud
from app.models import Role, UserCreate
from app.permissions import AVAILABLE_SCOPES, ROLE_TEMPLATES


TEST_PASSWORD = "role-test-password"


def _headers_for_scopes(
    client: TestClient, db: Session, scopes: list[str]
) -> dict[str, str]:
    email = "role-scope-user@example.com"
    user = db_crud.create_user(
        session=db,
        user_create=UserCreate(email=email, password=TEST_PASSWORD),
    )
    user.custom_scopes = scopes
    db.add(user)
    db.commit()

    response = client.post(
        "/login/access-token",
        data={"username": email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_role(
    client: TestClient,
    headers: dict[str, str],
    *,
    name: str,
    description: str = "Role created by an API test",
    scopes: list[str] | None = None,
) -> dict[str, object]:
    response = client.post(
        "/roles/",
        headers=headers,
        json={
            "name": name,
            "description": description,
            "scopes": scopes if scopes is not None else ["recipes:read"],
        },
    )
    assert response.status_code == 200
    return response.json()


def test_role_endpoints_require_authentication(client: TestClient) -> None:
    response = client.get("/roles/")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("GET", "/roles/", None),
        (
            "POST",
            "/roles/",
            {"name": "Forbidden role", "scopes": ["recipes:read"]},
        ),
        ("GET", f"/roles/{uuid.uuid4()}", None),
        ("PUT", f"/roles/{uuid.uuid4()}", {"name": "Forbidden update"}),
        ("DELETE", f"/roles/{uuid.uuid4()}", None),
        ("GET", "/roles/templates/", None),
        ("POST", "/roles/from-template/viewer", None),
        ("GET", "/roles/scopes/available", None),
    ],
)
def test_role_endpoints_reject_user_without_scopes(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    method: str,
    path: str,
    payload: dict[str, object] | None,
) -> None:
    response = client.request(
        method,
        path,
        headers=normal_user_token_headers,
        json=payload,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Not enough permissions"}


def test_read_scope_allows_role_metadata_but_not_creation(
    client: TestClient, db: Session
) -> None:
    headers = _headers_for_scopes(client, db, ["roles:read"])

    assert client.get("/roles/", headers=headers).status_code == 200
    assert client.get("/roles/templates/", headers=headers).status_code == 200
    assert client.get("/roles/scopes/available", headers=headers).status_code == 200

    response = client.post(
        "/roles/",
        headers=headers,
        json={"name": "Reader cannot create", "scopes": []},
    )
    assert response.status_code == 403


def test_role_crud_lifecycle(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    created = _create_role(
        client,
        superuser_token_headers,
        name="API lifecycle role",
        scopes=["recipes:read", "ingredients:read"],
    )
    role_id = created["id"]
    assert uuid.UUID(str(role_id))
    assert created == {
        "id": role_id,
        "name": "API lifecycle role",
        "description": "Role created by an API test",
        "scopes": ["recipes:read", "ingredients:read"],
    }

    get_response = client.get(f"/roles/{role_id}", headers=superuser_token_headers)
    assert get_response.status_code == 200
    assert get_response.json() == created

    list_response = client.get("/roles/", headers=superuser_token_headers)
    assert list_response.status_code == 200
    assert created in list_response.json()

    update_response = client.put(
        f"/roles/{role_id}",
        headers=superuser_token_headers,
        json={
            "name": "Updated API lifecycle role",
            "description": "Updated description",
            "scopes": ["roles:read"],
        },
    )
    assert update_response.status_code == 200
    assert update_response.json() == {
        "id": role_id,
        "name": "Updated API lifecycle role",
        "description": "Updated description",
        "scopes": ["roles:read"],
    }

    delete_response = client.delete(
        f"/roles/{role_id}", headers=superuser_token_headers
    )
    assert delete_response.status_code == 200
    assert delete_response.json() == {
        "message": "Role 'Updated API lifecycle role' deleted successfully"
    }

    missing_response = client.get(f"/roles/{role_id}", headers=superuser_token_headers)
    assert missing_response.status_code == 404
    assert missing_response.json() == {"detail": "Role not found"}


def test_create_role_rejects_duplicate_name(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    _create_role(client, superuser_token_headers, name="Duplicate role")

    response = client.post(
        "/roles/",
        headers=superuser_token_headers,
        json={"name": "Duplicate role", "scopes": []},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Role 'Duplicate role' already exists"}


def test_create_role_rejects_invalid_scope(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    response = client.post(
        "/roles/",
        headers=superuser_token_headers,
        json={"name": "Invalid scope role", "scopes": ["roles:not-real"]},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid scopes: roles:not-real"}
    assert (
        db.exec(select(Role).where(Role.name == "Invalid scope role")).first() is None
    )


def test_update_role_rejects_invalid_scope_without_changing_role(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    created = _create_role(
        client,
        superuser_token_headers,
        name="Unchanged invalid scope role",
        scopes=["recipes:read"],
    )

    response = client.put(
        f"/roles/{created['id']}",
        headers=superuser_token_headers,
        json={"scopes": ["roles:not-real"]},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid scopes: roles:not-real"}
    get_response = client.get(
        f"/roles/{created['id']}", headers=superuser_token_headers
    )
    assert get_response.status_code == 200
    assert get_response.json() == created


def test_update_role_rejects_name_conflict(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    _create_role(client, superuser_token_headers, name="Existing role name")
    role_to_update = _create_role(
        client, superuser_token_headers, name="Role with original name"
    )

    response = client.put(
        f"/roles/{role_to_update['id']}",
        headers=superuser_token_headers,
        json={"name": "Existing role name"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Role 'Existing role name' already exists"}
    get_response = client.get(
        f"/roles/{role_to_update['id']}", headers=superuser_token_headers
    )
    assert get_response.status_code == 200
    assert get_response.json() == role_to_update


@pytest.mark.parametrize(
    ("method", "payload"),
    [
        ("GET", None),
        ("PUT", {"name": "Missing role"}),
        ("DELETE", None),
    ],
)
def test_role_detail_endpoints_return_not_found(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    method: str,
    payload: dict[str, object] | None,
) -> None:
    response = client.request(
        method,
        f"/roles/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=payload,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Role not found"}


def test_list_role_templates(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get("/roles/templates/", headers=superuser_token_headers)

    assert response.status_code == 200
    assert response.json() == {"templates": ROLE_TEMPLATES}


def test_list_available_scopes(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get("/roles/scopes/available", headers=superuser_token_headers)

    assert response.status_code == 200
    scopes = response.json()["scopes"]
    assert scopes == sorted(AVAILABLE_SCOPES)
    assert len(scopes) == len(set(scopes))


def test_create_role_from_template_is_idempotent(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    first_response = client.post(
        "/roles/from-template/viewer", headers=superuser_token_headers
    )
    second_response = client.post(
        "/roles/from-template/viewer", headers=superuser_token_headers
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json() == first_response.json()
    assert first_response.json() == {
        "id": first_response.json()["id"],
        **ROLE_TEMPLATES["viewer"],
    }
    viewer_roles = db.exec(select(Role).where(Role.name == "Viewer")).all()
    assert len(viewer_roles) == 1


def test_create_role_from_unknown_template(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        "/roles/from-template/does-not-exist", headers=superuser_token_headers
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Unknown role template: does-not-exist"}
