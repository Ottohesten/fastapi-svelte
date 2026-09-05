from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import db_crud, security
from app.models import (
    Ingredient,
    NutritionEntry,
    Recipe,
    RecipeIngredientLink,
    User,
    UserCreate,
)
from app.routers import products as products_router
from tests.utils.utils import random_email, random_lower_string

LOG_DATE = date(2026, 9, 3)


def _user_headers(db: Session, scopes: list[str]) -> tuple[User, dict[str, str]]:
    user = db_crud.create_user(
        session=db,
        user_create=UserCreate(
            email=random_email(),
            password=random_lower_string(),
        ),
    )
    user.custom_scopes = scopes
    db.add(user)
    db.commit()
    token = security.create_access_token(
        {"sub": user.email, "scopes": scopes}, expires_delta=timedelta(minutes=10)
    )
    return user, {"Authorization": f"Bearer {token}"}


def _product_payload(**updates: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Freezer pizza",
        "brand": "Test Brand",
        "barcode": "12345678",
        "nutrition_basis": "per_100g",
        "calories": 250,
        "carbohydrates": 30,
        "fat": None,
        "protein": 10,
        "package_size": 400,
        "package_size_unit": "g",
    }
    payload.update(updates)
    return payload


def test_nutrition_scope_is_required(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    assert (
        client.get("/products/", headers=normal_user_token_headers).status_code == 403
    )
    assert (
        client.get(
            f"/nutrition/day/{LOG_DATE}", headers=normal_user_token_headers
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/nutrition/common-entries", headers=normal_user_token_headers
        ).status_code
        == 403
    )


def test_common_entries_are_history_derived_ranked_and_owner_scoped(
    client: TestClient, db: Session
) -> None:
    _, headers = _user_headers(db, ["nutrition:use"])
    _, other_headers = _user_headers(db, ["nutrition:use"])
    ingredient = Ingredient(
        title="Frequent oats",
        calories=350,
        carbohydrates=60,
        fat=8,
        protein=12,
        weight_per_piece=0,
    )
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)

    ingredient_payload = {
        "source_type": "ingredient",
        "source_id": str(ingredient.id),
        "log_date": str(LOG_DATE),
        "meal_type": "breakfast",
        "quantity": 100,
        "unit": "g",
    }
    for _ in range(2):
        response = client.post(
            "/nutrition/entries", headers=headers, json=ingredient_payload
        )
        assert response.status_code == 201
    for _ in range(4):
        response = client.post(
            "/nutrition/entries", headers=other_headers, json=ingredient_payload
        )
        assert response.status_code == 201

    once_only = {**ingredient_payload, "quantity": 50}
    assert (
        client.post("/nutrition/entries", headers=headers, json=once_only).status_code
        == 201
    )
    manual_payload = {
        "source_type": "manual",
        "title": "Mango smoothie",
        "brand": None,
        "calories": 240,
        "carbohydrates": None,
        "fat": 3,
        "protein": 8,
        "log_date": str(LOG_DATE),
        "meal_type": "snack",
        "quantity": 1,
        "unit": "piece",
    }
    for title in ("Mango smoothie", "  mango   smoothie  ", "MANGO SMOOTHIE"):
        response = client.post(
            "/nutrition/entries",
            headers=headers,
            json={**manual_payload, "title": title},
        )
        assert response.status_code == 201
    assert (
        client.post(
            "/nutrition/entries",
            headers=headers,
            json={**manual_payload, "calories": 300},
        ).status_code
        == 201
    )

    ingredient.title = "Updated frequent oats"
    ingredient.calories = 999
    db.add(ingredient)
    db.commit()

    response = client.get(
        "/nutrition/common-entries", headers=headers, params={"limit": 2}
    )
    assert response.status_code == 200
    common = response.json()["entries"]
    assert [(entry["source_type"], entry["use_count"]) for entry in common] == [
        ("manual", 3),
        ("ingredient", 2),
    ]
    assert common[0]["source_id"] is None
    assert common[0]["quantity"] == 1
    assert common[0]["unit"] == "piece"
    assert common[0]["carbohydrates"] is None
    assert common[0]["last_used_at"]
    assert common[1]["source_id"] == str(ingredient.id)
    assert common[1]["title"] == "Updated frequent oats"
    assert common[1]["quantity"] == 100
    assert common[1]["calories"] == 999


def test_products_are_private_searchable_and_barcode_unique_per_owner(
    client: TestClient, db: Session
) -> None:
    _, first_headers = _user_headers(db, ["nutrition:use"])
    _, second_headers = _user_headers(db, ["nutrition:use"])

    created = client.post("/products/", headers=first_headers, json=_product_payload())
    assert created.status_code == 201
    product_id = created.json()["id"]

    for query in ("Freezer", "Test Brand", "12345678"):
        response = client.get(
            "/products/", headers=first_headers, params={"query": query}
        )
        assert [item["id"] for item in response.json()] == [product_id]

    duplicate = client.post(
        "/products/", headers=first_headers, json=_product_payload()
    )
    assert duplicate.status_code == 409
    other_owner = client.post(
        "/products/", headers=second_headers, json=_product_payload()
    )
    assert other_owner.status_code == 201
    assert (
        client.get(f"/products/{product_id}", headers=second_headers).status_code == 404
    )


def test_saved_barcode_lookup_is_owner_scoped_and_does_not_call_upstream(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, headers = _user_headers(db, ["nutrition:use"])
    product = client.post("/products/", headers=headers, json=_product_payload()).json()

    def unexpected_lookup(_barcode: str):
        raise AssertionError(
            "Saved products must be resolved before an upstream lookup"
        )

    monkeypatch.setattr(products_router, "lookup_product_draft", unexpected_lookup)
    response = client.get("/products/barcode/12345678", headers=headers)

    assert response.status_code == 200
    assert response.json()["existing_product_id"] == product["id"]
    assert response.json()["needs_review"] is False


def test_product_patch_returns_serializable_validation_errors(
    client: TestClient, db: Session
) -> None:
    _, headers = _user_headers(db, ["nutrition:use"])
    product = client.post(
        "/products/",
        headers=headers,
        json=_product_payload(package_size=None, package_size_unit=None),
    ).json()

    response = client.patch(
        f"/products/{product['id']}",
        headers=headers,
        json={"serving_size": 50},
    )

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


def test_mixed_batch_totals_and_atomic_failure(client: TestClient, db: Session) -> None:
    user, headers = _user_headers(db, ["nutrition:use"])
    ingredient = Ingredient(
        title="Rice",
        calories=350,
        carbohydrates=75,
        fat=1,
        protein=7,
        weight_per_piece=0,
    )
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)

    response = client.post(
        "/nutrition/entries/batch",
        headers=headers,
        json={
            "entries": [
                {
                    "source_type": "ingredient",
                    "source_id": str(ingredient.id),
                    "log_date": str(LOG_DATE),
                    "meal_type": "lunch",
                    "quantity": 100,
                    "unit": "g",
                },
                {
                    "source_type": "manual",
                    "title": "Birthday cake",
                    "calories": 420,
                    "carbohydrates": None,
                    "fat": None,
                    "protein": None,
                    "log_date": str(LOG_DATE),
                    "meal_type": "snack",
                    "quantity": 1,
                    "unit": "piece",
                },
            ]
        },
    )
    assert response.status_code == 201

    day = client.get(f"/nutrition/day/{LOG_DATE}", headers=headers).json()
    assert [group["meal_type"] for group in day["groups"]] == [
        "breakfast",
        "lunch",
        "dinner",
        "snack",
    ]
    assert day["totals"]["calories"] == 770
    assert day["totals"]["carbohydrates"] == 75
    assert day["totals"]["carbohydrates_unknown"] is True
    assert day["totals"]["incomplete_entry_count"] == 1

    before = len(
        db.exec(select(NutritionEntry).where(NutritionEntry.owner_id == user.id)).all()
    )
    failed = client.post(
        "/nutrition/entries/batch",
        headers=headers,
        json={
            "entries": [
                {
                    "source_type": "manual",
                    "title": "Should roll back",
                    "calories": 10,
                    "log_date": str(LOG_DATE),
                    "meal_type": "snack",
                    "quantity": 1,
                    "unit": "piece",
                },
                {
                    "source_type": "ingredient",
                    "source_id": str(uuid.uuid4()),
                    "log_date": str(LOG_DATE),
                    "meal_type": "snack",
                    "quantity": 10,
                    "unit": "g",
                },
            ]
        },
    )
    assert failed.status_code == 404
    db.expire_all()
    after = len(
        db.exec(select(NutritionEntry).where(NutritionEntry.owner_id == user.id)).all()
    )
    assert after == before


def test_product_snapshot_survives_update_and_delete(
    client: TestClient, db: Session
) -> None:
    _, headers = _user_headers(db, ["nutrition:use"])
    product = client.post("/products/", headers=headers, json=_product_payload()).json()
    entry_payload = {
        "source_type": "product",
        "source_id": product["id"],
        "log_date": str(LOG_DATE),
        "meal_type": "dinner",
        "quantity": 0.5,
        "unit": "package",
    }
    logged = client.post(
        "/nutrition/entries",
        headers=headers,
        json=entry_payload,
    )
    assert logged.status_code == 201
    assert logged.json()["calories"] == 500
    assert (
        client.post(
            "/nutrition/entries", headers=headers, json=entry_payload
        ).status_code
        == 201
    )

    changed = client.patch(
        f"/products/{product['id']}", headers=headers, json={"calories": 999}
    )
    assert changed.status_code == 200
    assert (
        client.delete(f"/products/{product['id']}", headers=headers).status_code == 200
    )

    entry = client.get(f"/nutrition/day/{LOG_DATE}", headers=headers).json()["groups"][
        2
    ]["entries"][0]
    assert entry["calories"] == 500
    assert entry["title"] == "Freezer pizza"
    assert entry["source_available"] is False
    assert client.get("/nutrition/common-entries", headers=headers).json() == {
        "entries": []
    }


def test_recipe_visibility_is_rechecked_for_day_source_link(
    client: TestClient, db: Session
) -> None:
    user, headers = _user_headers(db, ["nutrition:use"])
    ingredient = Ingredient(
        title="Oats", calories=400, carbohydrates=60, fat=8, protein=12
    )
    db.add(ingredient)
    db.flush()
    recipe = Recipe(
        title="Shared oats",
        instructions="Cook",
        servings=2,
        owner_id=user.id,
        is_hidden=False,
    )
    db.add(recipe)
    db.flush()
    db.add(
        RecipeIngredientLink(
            recipe_id=recipe.id,
            ingredient_id=ingredient.id,
            amount=100,
            unit="g",
        )
    )
    db.commit()

    entry_payload = {
        "source_type": "recipe",
        "source_id": str(recipe.id),
        "log_date": str(LOG_DATE),
        "meal_type": "breakfast",
        "quantity": 0.5,
        "unit": "serving",
    }
    response = client.post("/nutrition/entries", headers=headers, json=entry_payload)
    assert response.status_code == 201
    assert response.json()["calories"] == 100
    assert (
        client.post(
            "/nutrition/entries", headers=headers, json=entry_payload
        ).status_code
        == 201
    )

    other, _ = _user_headers(db, ["nutrition:use"])
    recipe.owner_id = other.id
    recipe.is_hidden = True
    db.add(recipe)
    db.commit()
    entry = client.get(f"/nutrition/day/{LOG_DATE}", headers=headers).json()["groups"][
        0
    ]["entries"][0]
    assert entry["calories"] == 100
    assert entry["source_available"] is False
    assert client.get("/nutrition/common-entries", headers=headers).json() == {
        "entries": []
    }


def test_quick_add_preview_is_review_only_and_calculates_exact_matches(
    client: TestClient, db: Session
) -> None:
    user, headers = _user_headers(db, ["nutrition:use"])
    product = client.post("/products/", headers=headers, json=_product_payload()).json()

    response = client.post(
        "/nutrition/quick-add/preview",
        headers=headers,
        json={
            "text": "Aftensmad:\n0,5 pakke produkt: Freezer pizza",
            "log_date": str(LOG_DATE),
            "default_meal": "snack",
        },
    )
    assert response.status_code == 200
    preview = response.json()
    assert preview["can_confirm"] is True
    assert preview["rows"][0]["source_id"] == product["id"]
    assert preview["rows"][0]["meal_type"] == "dinner"
    assert preview["rows"][0]["calories"] == 500
    assert (
        db.exec(
            select(NutritionEntry).where(NutritionEntry.owner_id == user.id)
        ).first()
        is None
    )


def test_preview_handles_legacy_unusable_titles_and_out_of_range_values(
    client: TestClient, db: Session
) -> None:
    _, headers = _user_headers(db, ["nutrition:use"])
    db.add(Ingredient(title="---", calories=0))
    db.commit()

    valid = client.post(
        "/nutrition/quick-add/preview",
        headers=headers,
        json={
            "text": "manual: Safe food | 100 kcal",
            "log_date": str(LOG_DATE),
            "default_meal": "snack",
        },
    )
    assert valid.status_code == 200
    assert valid.json()["rows"][0]["status"] == "resolved"

    too_long_name = "x" * 256
    invalid = client.post(
        "/nutrition/quick-add/preview",
        headers=headers,
        json={
            "text": f"manual: {too_long_name} | 100 kcal\nmanual: Huge | {'9' * 400} kcal",
            "log_date": str(LOG_DATE),
            "default_meal": "snack",
        },
    )
    assert invalid.status_code == 200
    assert [row["status"] for row in invalid.json()["rows"]] == [
        "invalid",
        "invalid",
    ]
    assert invalid.json()["can_confirm"] is False


def test_metadata_patch_rejects_null_date_and_meal(
    client: TestClient, db: Session
) -> None:
    _, headers = _user_headers(db, ["nutrition:use"])
    created = client.post(
        "/nutrition/entries",
        headers=headers,
        json={
            "source_type": "manual",
            "title": "Snack",
            "calories": 100,
            "log_date": str(LOG_DATE),
            "meal_type": "snack",
            "quantity": 1,
            "unit": "piece",
        },
    ).json()

    for body in ({"log_date": None}, {"meal_type": None}):
        response = client.patch(
            f"/nutrition/entries/{created['id']}", headers=headers, json=body
        )
        assert response.status_code == 422


def test_entry_mutations_are_owner_isolated(client: TestClient, db: Session) -> None:
    _, owner_headers = _user_headers(db, ["nutrition:use"])
    _, other_headers = _user_headers(db, ["nutrition:use"])
    created = client.post(
        "/nutrition/entries",
        headers=owner_headers,
        json={
            "source_type": "manual",
            "title": "Private snack",
            "calories": 100,
            "log_date": str(LOG_DATE),
            "meal_type": "snack",
            "quantity": 1,
            "unit": "piece",
        },
    ).json()
    entry_path = f"/nutrition/entries/{created['id']}"

    assert (
        client.patch(
            entry_path, headers=other_headers, json={"meal_type": "dinner"}
        ).status_code
        == 404
    )
    assert (
        client.put(
            entry_path,
            headers=other_headers,
            json={
                "source_type": "manual",
                "title": "Stolen snack",
                "calories": 1,
                "log_date": str(LOG_DATE),
                "meal_type": "snack",
                "quantity": 1,
                "unit": "piece",
            },
        ).status_code
        == 404
    )
    assert client.delete(entry_path, headers=other_headers).status_code == 404

    owner_day = client.get(f"/nutrition/day/{LOG_DATE}", headers=owner_headers).json()
    assert owner_day["totals"]["calories"] == 100


def test_recipe_and_ingredient_deletion_preserve_entry_snapshots(
    client: TestClient, db: Session
) -> None:
    user, headers = _user_headers(db, ["nutrition:use", "ingredients:delete"])
    ingredient = Ingredient(
        title="Disposable oats",
        calories=400,
        carbohydrates=60,
        fat=8,
        protein=12,
    )
    db.add(ingredient)
    db.flush()
    recipe = Recipe(
        title="Disposable porridge",
        instructions="Cook",
        servings=2,
        owner_id=user.id,
    )
    db.add(recipe)
    db.flush()
    db.add(
        RecipeIngredientLink(
            recipe_id=recipe.id,
            ingredient_id=ingredient.id,
            amount=100,
            unit="g",
        )
    )
    db.commit()

    payloads = [
        {
            "source_type": "recipe",
            "source_id": str(recipe.id),
            "log_date": str(LOG_DATE),
            "meal_type": "breakfast",
            "quantity": 1,
            "unit": "serving",
        },
        {
            "source_type": "ingredient",
            "source_id": str(ingredient.id),
            "log_date": str(LOG_DATE),
            "meal_type": "breakfast",
            "quantity": 100,
            "unit": "g",
        },
    ]
    for payload in payloads:
        assert (
            client.post("/nutrition/entries", headers=headers, json=payload).status_code
            == 201
        )

    assert client.delete(f"/recipes/{recipe.id}", headers=headers).status_code == 200
    assert (
        client.delete(f"/ingredients/{ingredient.id}", headers=headers).status_code
        == 200
    )

    entries = client.get(f"/nutrition/day/{LOG_DATE}", headers=headers).json()[
        "groups"
    ][0]["entries"]
    assert [(entry["title"], entry["calories"]) for entry in entries] == [
        ("Disposable porridge", 200),
        ("Disposable oats", 400),
    ]
    assert all(entry["source_id"] is None for entry in entries)
    assert all(entry["source_available"] is False for entry in entries)
