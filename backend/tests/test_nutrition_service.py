from __future__ import annotations

import uuid
from datetime import date
from typing import cast

import pytest
from pydantic import ValidationError
from sqlmodel import Session

from app.models import (
    Ingredient,
    IngredientNutritionEntryCreate,
    ManualNutritionEntryCreate,
    NutritionEntryMoveUpdate,
    NutritionEntryUnit,
    Product,
    ProductCreate,
    ProductNutritionBasis,
    ProductNutritionEntryCreate,
    Recipe,
    RecipeIngredientLink,
    RecipeNutritionEntryCreate,
    User,
)
from app.nutrition_service import NutritionInputError, calculate_entry

pytestmark = pytest.mark.no_db


class FakeSession:
    def __init__(self, *objects: object):
        self.objects: dict[tuple[type, object], object] = {}
        for item in objects:
            item_id = getattr(item, "id", None)
            if item_id is not None:
                self.objects[(type(item), item_id)] = item

    def get(self, model: type, object_id: uuid.UUID):
        return self.objects.get((model, object_id))


def _session(*objects: object) -> Session:
    """Expose the deliberately small test double through the production boundary type."""
    return cast(Session, FakeSession(*objects))


def _user() -> User:
    return User(
        id=uuid.uuid4(),
        email="nutrition@example.com",
        hashed_password="unused",
    )


def _product(user: User, **updates: object) -> Product:
    data = {
        "id": uuid.uuid4(),
        "owner_id": user.id,
        "title": "Test product",
        "nutrition_basis": ProductNutritionBasis.PER_100G,
        "calories": 250,
        "carbohydrates": 40,
        "fat": None,
        "protein": 10,
    }
    data.update(updates)
    return Product.model_validate(data)


def _product_payload(product: Product, quantity: float, unit: str):
    return ProductNutritionEntryCreate(
        source_type="product",
        source_id=product.id,
        log_date=date(2026, 9, 3),
        meal_type="lunch",
        quantity=quantity,
        unit=unit,
    )


def test_product_package_converts_through_saved_mass() -> None:
    user = _user()
    product = _product(user, package_size=400, package_size_unit="g")

    result = calculate_entry(
        _session(product), user, _product_payload(product, 0.5, "package")
    )

    assert result.calories == 500
    assert result.carbohydrates == 80
    assert result.fat is None
    assert result.protein == 20


def test_product_serving_basis_supports_direct_and_physical_amounts() -> None:
    user = _user()
    product = _product(
        user,
        nutrition_basis="per_serving",
        calories=125,
        serving_size=50,
        serving_size_unit="g",
    )

    direct = calculate_entry(
        _session(product), user, _product_payload(product, 1.5, "serving")
    )
    physical = calculate_entry(
        _session(product), user, _product_payload(product, 100, "g")
    )

    assert direct.calories == 187.5
    assert physical.calories == 250


def test_product_rejects_mass_volume_guess() -> None:
    user = _user()
    product = _product(user, nutrition_basis="per_100ml")

    with pytest.raises(NutritionInputError, match="millilitres"):
        calculate_entry(_session(product), user, _product_payload(product, 100, "g"))


def test_product_per_100ml_supports_direct_volume() -> None:
    user = _user()
    product = _product(
        user,
        nutrition_basis="per_100ml",
        calories=42,
        carbohydrates=5,
        protein=2,
    )

    result = calculate_entry(
        _session(product), user, _product_payload(product, 250, "ml")
    )

    assert result.calories == 105
    assert result.carbohydrates == 12.5


def test_product_per_package_supports_direct_and_saved_size_conversions() -> None:
    user = _user()
    product = _product(
        user,
        nutrition_basis="per_package",
        calories=600,
        package_size=300,
        package_size_unit="g",
    )

    direct = calculate_entry(
        _session(product), user, _product_payload(product, 0.5, "package")
    )
    physical = calculate_entry(
        _session(product), user, _product_payload(product, 100, "g")
    )

    assert direct.calories == 300
    assert physical.calories == 200


def test_product_conversion_rejects_missing_saved_size() -> None:
    user = _user()
    product = _product(user)

    with pytest.raises(NutritionInputError, match="package size"):
        calculate_entry(
            _session(product), user, _product_payload(product, 1, "package")
        )


def test_ingredient_supports_grams_and_piece_weight_but_not_volume() -> None:
    user = _user()
    ingredient = Ingredient(
        id=uuid.uuid4(),
        title="Egg",
        calories=150,
        carbohydrates=1,
        fat=10,
        protein=12,
        weight_per_piece=60,
    )
    piece = calculate_entry(
        _session(ingredient),
        user,
        IngredientNutritionEntryCreate(
            source_type="ingredient",
            source_id=ingredient.id,
            log_date=date(2026, 9, 3),
            meal_type="breakfast",
            quantity=2,
            unit="piece",
        ),
    )

    assert piece.calories == 180
    assert piece.protein == pytest.approx(14.4)
    with pytest.raises(NutritionInputError, match="without density"):
        calculate_entry(
            _session(ingredient),
            user,
            IngredientNutritionEntryCreate(
                source_type="ingredient",
                source_id=ingredient.id,
                log_date=date(2026, 9, 3),
                meal_type="breakfast",
                quantity=100,
                unit="ml",
            ),
        )


def test_recipe_fractional_serving_uses_unrounded_total() -> None:
    user = _user()
    ingredient = Ingredient(
        id=uuid.uuid4(),
        title="Precise ingredient",
        calories=101,
        carbohydrates=9.9,
        fat=2.2,
        protein=3.3,
    )
    recipe = Recipe(
        id=uuid.uuid4(),
        title="Precise recipe",
        instructions="",
        servings=3,
        owner_id=user.id,
    )
    link = RecipeIngredientLink(
        recipe_id=recipe.id,
        ingredient_id=ingredient.id,
        amount=100,
        unit="g",
    )
    link.ingredient = ingredient
    recipe.ingredient_links = [link]
    payload = RecipeNutritionEntryCreate(
        source_type="recipe",
        source_id=recipe.id,
        log_date=date(2026, 9, 3),
        meal_type="dinner",
        quantity=0.5,
        unit="serving",
    )

    result = calculate_entry(_session(recipe), user, payload)

    assert result.calories == pytest.approx(101 / 6)
    assert result.carbohydrates == pytest.approx(9.9 / 6)


def test_manual_totals_keep_unknown_macros() -> None:
    result = calculate_entry(
        _session(),
        _user(),
        ManualNutritionEntryCreate(
            source_type="manual",
            title="Cake",
            calories=420,
            carbohydrates=48,
            fat=None,
            protein=None,
            log_date=date(2026, 9, 3),
            meal_type="snack",
            quantity=1,
            unit=NutritionEntryUnit.PIECE,
        ),
    )

    assert result.calories == 420
    assert result.fat is None
    assert result.protein is None


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_product_api_models_reject_non_finite_values(value: float) -> None:
    with pytest.raises(ValidationError):
        ProductCreate(title="Impossible", calories=value)


def test_product_and_manual_titles_cannot_be_only_whitespace() -> None:
    with pytest.raises(ValidationError):
        ProductCreate(title="   ", calories=100)

    with pytest.raises(ValidationError):
        ManualNutritionEntryCreate(
            source_type="manual",
            title="   ",
            calories=100,
            log_date=date(2026, 9, 3),
            meal_type="snack",
            quantity=1,
            unit="piece",
        )


@pytest.mark.parametrize("field", ["log_date", "meal_type"])
def test_metadata_patch_rejects_explicit_null_location(field: str) -> None:
    with pytest.raises(ValidationError):
        NutritionEntryMoveUpdate.model_validate({field: None})
