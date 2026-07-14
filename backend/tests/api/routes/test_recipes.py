from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import db_crud
from app.models import Ingredient, User, UserCreate
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


def _ingredient(
    db: Session,
    *,
    title: str = "Flour",
    calories: int = 350,
    weight_per_piece: int = 100,
) -> Ingredient:
    ingredient = Ingredient(
        title=title,
        calories=calories,
        carbohydrates=70,
        fat=2,
        protein=10,
        weight_per_piece=weight_per_piece,
    )
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return ingredient


def _user_and_headers(client: TestClient, db: Session) -> tuple[User, dict[str, str]]:
    password = random_lower_string()
    user = db_crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=password),
    )
    headers = user_authentication_headers(
        client=client,
        email=user.email,
        password=password,
    )
    return user, headers


def _payload(
    ingredient_id: UUID,
    *,
    title: str = "Test recipe",
    hidden: bool = False,
    viewer_ids: list[str] | None = None,
    sub_recipes: list[dict] | None = None,
) -> dict:
    return {
        "title": title,
        "instructions": "Mix and cook.",
        "servings": 2,
        "image": None,
        "is_hidden": hidden,
        "ingredients": [
            {
                "ingredient_id": str(ingredient_id),
                "amount": 200,
                "consumed_amount": 150,
                "unit": "g",
            }
        ],
        "sub_recipes": sub_recipes or [],
        "viewer_ids": viewer_ids,
    }


def _create_recipe(
    client: TestClient,
    headers: dict[str, str],
    payload: dict,
) -> dict:
    response = client.post("/recipes/", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_recipe_crud_and_nutrition(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    ingredient = _ingredient(db)
    payload = _payload(ingredient.id)
    recipe = _create_recipe(client, superuser_token_headers, payload)

    assert recipe["title"] == "Test recipe"
    assert recipe["ingredient_links"][0]["amount"] == 200
    assert recipe["ingredient_links"][0]["consumed_amount"] == 150
    assert recipe["total_calories"] == 525
    assert recipe["calories_per_serving"] == 262

    get_response = client.get(f"/recipes/{recipe['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == recipe["id"]

    list_response = client.get("/recipes/")
    assert list_response.status_code == 200
    assert recipe["id"] in {item["id"] for item in list_response.json()}

    payload["title"] = "Updated recipe"
    payload["ingredients"][0]["amount"] = 250
    update_response = client.patch(
        f"/recipes/{recipe['id']}",
        headers=superuser_token_headers,
        json=payload,
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated recipe"
    assert update_response.json()["ingredient_links"][0]["amount"] == 250

    delete_response = client.delete(
        f"/recipes/{recipe['id']}", headers=superuser_token_headers
    )
    assert delete_response.status_code == 200

    missing_response = client.get(f"/recipes/{recipe['id']}")
    assert missing_response.status_code == 404


def test_recipe_create_requires_scope(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    ingredient = _ingredient(db)
    response = client.post(
        "/recipes/",
        headers=normal_user_token_headers,
        json=_payload(ingredient.id),
    )
    assert response.status_code == 403


def test_hidden_recipe_visibility_and_viewer_id_disclosure(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    ingredient = _ingredient(db)
    viewer, viewer_headers = _user_and_headers(client, db)
    _, unrelated_headers = _user_and_headers(client, db)
    recipe = _create_recipe(
        client,
        superuser_token_headers,
        _payload(
            ingredient.id,
            hidden=True,
            viewer_ids=[str(viewer.id)],
        ),
    )

    anonymous_response = client.get(f"/recipes/{recipe['id']}")
    assert anonymous_response.status_code == 404

    unrelated_response = client.get(
        f"/recipes/{recipe['id']}", headers=unrelated_headers
    )
    assert unrelated_response.status_code == 404

    viewer_response = client.get(f"/recipes/{recipe['id']}", headers=viewer_headers)
    assert viewer_response.status_code == 200
    assert viewer_response.json()["viewer_ids"] is None

    owner_response = client.get(
        f"/recipes/{recipe['id']}", headers=superuser_token_headers
    )
    assert owner_response.status_code == 200
    assert owner_response.json()["viewer_ids"] == [str(viewer.id)]

    anonymous_list = client.get("/recipes/").json()
    assert recipe["id"] not in {item["id"] for item in anonymous_list}
    viewer_list = client.get("/recipes/", headers=viewer_headers).json()
    assert recipe["id"] in {item["id"] for item in viewer_list}


def test_unrelated_user_cannot_update_or_delete_recipe(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    ingredient = _ingredient(db)
    _, unrelated_headers = _user_and_headers(client, db)
    payload = _payload(ingredient.id)
    recipe = _create_recipe(client, superuser_token_headers, payload)

    update_response = client.patch(
        f"/recipes/{recipe['id']}", headers=unrelated_headers, json=payload
    )
    assert update_response.status_code == 403

    delete_response = client.delete(
        f"/recipes/{recipe['id']}", headers=unrelated_headers
    )
    assert delete_response.status_code == 403


def test_create_recipe_rejects_missing_ingredient(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        "/recipes/",
        headers=superuser_token_headers,
        json=_payload(uuid4()),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Ingredient not found"


def test_update_recipe_rejects_missing_ingredient(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    ingredient = _ingredient(db)
    recipe = _create_recipe(client, superuser_token_headers, _payload(ingredient.id))

    response = client.patch(
        f"/recipes/{recipe['id']}",
        headers=superuser_token_headers,
        json=_payload(uuid4()),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Ingredient not found"


def test_recipe_rejects_duplicate_ingredients(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    ingredient = _ingredient(db)
    payload = _payload(ingredient.id)
    payload["ingredients"].append(dict(payload["ingredients"][0]))

    response = client.post("/recipes/", headers=superuser_token_headers, json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Each ingredient can only appear once in a recipe"
    )


def test_recipe_requires_positive_servings(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    ingredient = _ingredient(db)
    payload = _payload(ingredient.id)
    payload["servings"] = 0

    response = client.post("/recipes/", headers=superuser_token_headers, json=payload)
    assert response.status_code == 422


def test_sub_recipe_totals_are_scaled(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    ingredient = _ingredient(db, calories=100)
    child = _create_recipe(
        client,
        superuser_token_headers,
        _payload(ingredient.id, title="Child"),
    )
    parent = _create_recipe(
        client,
        superuser_token_headers,
        _payload(
            ingredient.id,
            title="Parent",
            sub_recipes=[{"sub_recipe_id": child["id"], "scale_factor": 0.5}],
        ),
    )

    total = parent["total_ingredients"][0]
    assert total["amount"] == 300
    assert total["consumed_amount"] == 225
    assert total["source_count"] == 2
    assert total["has_overlap"] is True


def test_duplicate_and_missing_sub_recipes_are_rejected(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    ingredient = _ingredient(db)
    child = _create_recipe(
        client,
        superuser_token_headers,
        _payload(ingredient.id, title="Child"),
    )
    duplicate_link = {"sub_recipe_id": child["id"], "scale_factor": 1}
    payload = _payload(
        ingredient.id,
        sub_recipes=[duplicate_link, duplicate_link],
    )

    duplicate_response = client.post(
        "/recipes/", headers=superuser_token_headers, json=payload
    )
    assert duplicate_response.status_code == 400


def test_missing_sub_recipe_is_rejected(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    ingredient = _ingredient(db)
    response = client.post(
        "/recipes/",
        headers=superuser_token_headers,
        json=_payload(
            ingredient.id,
            sub_recipes=[{"sub_recipe_id": str(uuid4()), "scale_factor": 1}],
        ),
    )
    assert response.status_code == 404


def test_sub_recipe_self_reference_and_cycle_are_rejected(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    ingredient = _ingredient(db)
    first_payload = _payload(ingredient.id, title="First")
    first = _create_recipe(client, superuser_token_headers, first_payload)
    second_payload = _payload(
        ingredient.id,
        title="Second",
        sub_recipes=[{"sub_recipe_id": first["id"], "scale_factor": 1}],
    )
    second = _create_recipe(client, superuser_token_headers, second_payload)

    first_payload["sub_recipes"] = [{"sub_recipe_id": first["id"], "scale_factor": 1}]
    self_response = client.patch(
        f"/recipes/{first['id']}",
        headers=superuser_token_headers,
        json=first_payload,
    )
    assert self_response.status_code == 400

    first_payload["sub_recipes"] = [{"sub_recipe_id": second["id"], "scale_factor": 1}]
    cycle_response = client.patch(
        f"/recipes/{first['id']}",
        headers=superuser_token_headers,
        json=first_payload,
    )
    assert cycle_response.status_code == 400


def test_invalid_viewer_and_owner_as_viewer(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    ingredient = _ingredient(db)
    invalid_response = client.post(
        "/recipes/",
        headers=superuser_token_headers,
        json=_payload(ingredient.id, hidden=True, viewer_ids=[str(uuid4())]),
    )
    assert invalid_response.status_code == 404


def test_recipe_image_upload_rejects_non_image(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        "/recipes/upload-image",
        headers=superuser_token_headers,
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "File must be an image"
