import uuid

import pytest
from pydantic import ValidationError

from app.models import Ingredient, Recipe, RecipeIngredientLinkCreate
from app.routers.recipes import _add_ingredient_total


pytestmark = pytest.mark.no_db


def _recipe() -> Recipe:
    return Recipe(
        title="Deep-fried example",
        instructions="Fry until crisp.",
        servings=4,
        owner_id=uuid.uuid4(),
    )


def _oil() -> Ingredient:
    return Ingredient(
        title="Frying oil",
        calories=884,
        carbohydrates=0,
        fat=100,
        protein=0,
    )


def test_consumed_amount_cannot_exceed_recipe_amount() -> None:
    with pytest.raises(ValidationError, match="cannot exceed"):
        RecipeIngredientLinkCreate(
            ingredient_id=uuid.uuid4(),
            amount=1,
            consumed_amount=1.1,
            unit="L",
        )


def test_nutrition_uses_consumed_amount_but_keeps_required_amount() -> None:
    totals = {}
    source_totals = {}
    recipe = _recipe()

    _add_ingredient_total(
        totals,
        source_totals,
        _oil(),
        amount=1,
        consumed_amount=0.1,
        unit="L",
        source_recipe=recipe,
        is_main_recipe=True,
    )

    total = next(iter(totals.values()))
    assert total.amount == 1000
    assert total.consumed_amount == 100
    assert total.grams == 100
    assert total.calories == 884
    assert total.fat == 100


def test_missing_consumed_amount_defaults_to_full_amount() -> None:
    totals = {}
    source_totals = {}
    recipe = _recipe()

    _add_ingredient_total(
        totals,
        source_totals,
        _oil(),
        amount=250,
        consumed_amount=None,
        unit="g",
        source_recipe=recipe,
        is_main_recipe=True,
    )

    total = next(iter(totals.values()))
    assert total.amount == 250
    assert total.consumed_amount == 250
    assert total.calories == 2210
