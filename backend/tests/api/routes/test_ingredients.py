import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlmodel import Session, select

from app.config import settings
from app.models import (
    Ingredient,
    IngredientCreate,
    OpenFoodFactsProductPublic,
    Recipe,
    RecipeIngredientLink,
    User,
)
from app.openfoodfacts import OpenFoodFactsUnavailableError, ProductNotFoundError


def _ingredient_payload(
    *, title: str = "Test ingredient", barcode: str | None = None
) -> dict[str, object]:
    return {
        "title": title,
        "calories": 123,
        "carbohydrates": 12.5,
        "fat": 6.25,
        "protein": 3.5,
        "weight_per_piece": 75,
        "barcode": barcode,
    }


def _create_ingredient(
    db: Session, *, title: str = "Test ingredient", barcode: str | None = None
) -> Ingredient:
    ingredient_in = IngredientCreate.model_validate(
        _ingredient_payload(title=title, barcode=barcode)
    )
    ingredient = Ingredient.model_validate(ingredient_in)
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return ingredient


def _product(
    *, barcode: str = "00001234", title: str = "Scanned product"
) -> OpenFoodFactsProductPublic:
    return OpenFoodFactsProductPublic(
        barcode=barcode,
        title=title,
        brand="Test brand",
        image_url="https://images.example.test/product.jpg",
        calories=250,
        carbohydrates=30,
        fat=10,
        protein=5,
        weight_per_piece=100,
        nutrition_basis="100g",
        missing_nutrients=[],
    )


@pytest.mark.no_db
@pytest.mark.parametrize(
    ("raw_barcode", "normalized_barcode"),
    [
        (None, None),
        ("", None),
        (" 1234 ", "00001234"),
        ("01234567", "01234567"),
        ("123456789", "0000123456789"),
        ("1234567890123", "1234567890123"),
    ],
)
def test_ingredient_normalizes_barcodes(
    raw_barcode: str | None, normalized_barcode: str | None
) -> None:
    ingredient = IngredientCreate(title="Barcode test", barcode=raw_barcode)

    assert ingredient.barcode == normalized_barcode


@pytest.mark.no_db
@pytest.mark.parametrize(
    ("barcode", "message"),
    [
        ("123", "between 4 and 24 digits"),
        ("12a4", "between 4 and 24 digits"),
        ("1" * 25, "at most 24 characters"),
    ],
)
def test_ingredient_rejects_invalid_barcodes(barcode: str, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        IngredientCreate(title="Barcode test", barcode=barcode)


def test_create_get_and_list_ingredient(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        "/ingredients/",
        headers=superuser_token_headers,
        json=_ingredient_payload(barcode="1234"),
    )

    assert response.status_code == 200
    created = response.json()
    assert created["title"] == "Test ingredient"
    assert created["barcode"] == "00001234"
    assert created["calories"] == 123
    assert created["carbohydrates"] == 12.5
    assert created["fat"] == 6.25
    assert created["protein"] == 3.5
    assert created["weight_per_piece"] == 75

    get_response = client.get(f"/ingredients/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == created

    list_response = client.get("/ingredients/")
    assert list_response.status_code == 200
    assert created in list_response.json()


def test_get_ingredient_rejects_invalid_uuid(client: TestClient) -> None:
    response = client.get("/ingredients/not-a-uuid")

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid UUID"}


def test_get_ingredient_returns_not_found(client: TestClient) -> None:
    response = client.get(f"/ingredients/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Ingredient not found"}


def test_update_ingredient(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    ingredient = _create_ingredient(db, barcode="1234")
    update = _ingredient_payload(title="Updated ingredient", barcode="9876543210123")
    update["calories"] = 456

    response = client.patch(
        f"/ingredients/{ingredient.id}",
        headers=superuser_token_headers,
        json=update,
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "Updated ingredient"
    assert updated["calories"] == 456
    assert updated["barcode"] == "9876543210123"

    db.refresh(ingredient)
    assert ingredient.title == "Updated ingredient"
    assert ingredient.calories == 456
    assert ingredient.barcode == "9876543210123"


def test_update_ingredient_returns_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.patch(
        f"/ingredients/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=_ingredient_payload(),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Ingredient not found"}


def test_create_ingredient_rejects_duplicate_normalized_barcode(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    first_response = client.post(
        "/ingredients/",
        headers=superuser_token_headers,
        json=_ingredient_payload(title="First", barcode="1234"),
    )
    assert first_response.status_code == 200

    duplicate_response = client.post(
        "/ingredients/",
        headers=superuser_token_headers,
        json=_ingredient_payload(title="Duplicate", barcode="00001234"),
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "An ingredient with this barcode already exists"
    }


def test_update_ingredient_rejects_duplicate_barcode(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    first = _create_ingredient(db, title="First", barcode="1234")
    second = _create_ingredient(db, title="Second", barcode="5678")

    response = client.patch(
        f"/ingredients/{second.id}",
        headers=superuser_token_headers,
        json=_ingredient_payload(title="Second", barcode=first.barcode),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "An ingredient with this barcode already exists"
    }


def test_ingredient_mutations_require_their_scopes(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    ingredient = _create_ingredient(db)
    cases = (
        ("POST", "/ingredients/", _ingredient_payload(title="Denied create")),
        (
            "PATCH",
            f"/ingredients/{ingredient.id}",
            _ingredient_payload(title="Denied update"),
        ),
        ("DELETE", f"/ingredients/{ingredient.id}", None),
    )

    for method, path, body in cases:
        response = client.request(
            method,
            path,
            headers=normal_user_token_headers,
            json=body,
        )
        assert response.status_code == 403

    assert db.get(Ingredient, ingredient.id) is not None


def test_delete_ingredient_removes_recipe_link_but_keeps_recipe(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    ingredient = _create_ingredient(db)
    owner = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).one()
    recipe = Recipe(
        title="Linked recipe",
        instructions="Mix.",
        servings=1,
        owner_id=owner.id,
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
    recipe_id = recipe.id
    ingredient_id = ingredient.id

    response = client.delete(
        f"/ingredients/{ingredient_id}", headers=superuser_token_headers
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(ingredient_id)
    assert db.get(Ingredient, ingredient_id) is None
    assert db.get(Recipe, recipe_id) is not None
    links = db.exec(
        select(RecipeIngredientLink).where(
            RecipeIngredientLink.ingredient_id == ingredient_id
        )
    ).all()
    assert links == []


def test_delete_ingredient_returns_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"/ingredients/{uuid.uuid4()}", headers=superuser_token_headers
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Ingredient not found"}


def test_barcode_lookup_normalizes_input_and_maps_product(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_barcodes: list[str] = []

    def fake_lookup(barcode: str) -> OpenFoodFactsProductPublic:
        requested_barcodes.append(barcode)
        return _product(barcode=barcode)

    monkeypatch.setattr("app.routers.ingredients.lookup_product", fake_lookup)

    response = client.get("/ingredients/barcode/1234", headers=superuser_token_headers)

    assert response.status_code == 200
    assert requested_barcodes == ["00001234"]
    assert response.json() == {
        "barcode": "00001234",
        "title": "Scanned product",
        "brand": "Test brand",
        "image_url": "https://images.example.test/product.jpg",
        "calories": 250,
        "carbohydrates": 30.0,
        "fat": 10.0,
        "protein": 5.0,
        "weight_per_piece": 100,
        "nutrition_basis": "100g",
        "missing_nutrients": [],
        "existing_ingredient_id": None,
    }


def test_barcode_lookup_reports_existing_ingredient(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ingredient = _create_ingredient(db, barcode="1234")
    monkeypatch.setattr(
        "app.routers.ingredients.lookup_product",
        lambda barcode: _product(barcode=barcode),
    )

    response = client.get("/ingredients/barcode/1234", headers=superuser_token_headers)

    assert response.status_code == 200
    assert response.json()["existing_ingredient_id"] == str(ingredient.id)


@pytest.mark.parametrize(
    ("lookup_error", "status_code", "detail"),
    [
        (
            ProductNotFoundError(),
            404,
            "Product not found in Open Food Facts",
        ),
        (
            OpenFoodFactsUnavailableError(),
            503,
            "Open Food Facts is temporarily unavailable. Please try again.",
        ),
    ],
)
def test_barcode_lookup_translates_upstream_errors(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    lookup_error: Exception,
    status_code: int,
    detail: str,
) -> None:
    def fake_lookup(barcode: str) -> OpenFoodFactsProductPublic:
        raise lookup_error

    monkeypatch.setattr("app.routers.ingredients.lookup_product", fake_lookup)

    response = client.get("/ingredients/barcode/1234", headers=superuser_token_headers)

    assert response.status_code == status_code
    assert response.json() == {"detail": detail}


def test_barcode_lookup_rejects_invalid_input_before_external_call(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_lookup(barcode: str) -> OpenFoodFactsProductPublic:
        pytest.fail(f"Unexpected Open Food Facts lookup for {barcode}")

    monkeypatch.setattr("app.routers.ingredients.lookup_product", unexpected_lookup)

    response = client.get(
        "/ingredients/barcode/not-a-barcode", headers=superuser_token_headers
    )

    assert response.status_code == 422
    assert "between 4 and 24 digits" in response.json()["detail"]


def test_barcode_lookup_requires_create_scope_before_external_call(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_lookup(barcode: str) -> OpenFoodFactsProductPublic:
        pytest.fail(f"Unexpected Open Food Facts lookup for {barcode}")

    monkeypatch.setattr("app.routers.ingredients.lookup_product", unexpected_lookup)

    response = client.get(
        "/ingredients/barcode/1234", headers=normal_user_token_headers
    )

    assert response.status_code == 403
