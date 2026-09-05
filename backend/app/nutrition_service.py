from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlmodel import Session, col, select

from app.models import (
    Ingredient,
    IngredientNutritionEntryCreate,
    ManualNutritionEntryCreate,
    NutritionCommonEntriesPublic,
    NutritionCommonEntryPublic,
    NutritionEntry,
    NutritionEntryCreate,
    NutritionEntryPublic,
    NutritionEntryUnit,
    NutritionSourceType,
    Product,
    ProductNutritionBasis,
    ProductNutritionEntryCreate,
    Recipe,
    RecipeNutritionEntryCreate,
    User,
)
from app.recipe_service import calculate_recipe_nutrients, can_view_recipe


class NutritionInputError(ValueError):
    """The requested amount cannot be converted safely for its food source."""


class NutritionSourceNotFoundError(LookupError):
    """A requested source does not exist or is not visible to the caller."""


@dataclass(frozen=True, slots=True)
class CalculatedNutrition:
    title: str
    brand: str | None
    calories: float
    carbohydrates: float | None
    fat: float | None
    protein: float | None
    recipe_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    ingredient_id: uuid.UUID | None = None


@dataclass(slots=True)
class _CommonEntryGroup:
    entry: NutritionEntry
    use_count: int
    last_used_at: datetime


def calculate_entry(
    session: Session,
    user: User,
    payload: NutritionEntryCreate,
) -> CalculatedNutrition:
    if isinstance(payload, RecipeNutritionEntryCreate):
        return _calculate_recipe_entry(session, user, payload)
    if isinstance(payload, ProductNutritionEntryCreate):
        return _calculate_product_entry(session, user, payload)
    if isinstance(payload, IngredientNutritionEntryCreate):
        return _calculate_ingredient_entry(session, payload)
    if isinstance(payload, ManualNutritionEntryCreate):
        return _calculate_manual_entry(payload)
    raise TypeError("Unsupported nutrition entry payload")


def build_entry(
    session: Session,
    user: User,
    payload: NutritionEntryCreate,
) -> NutritionEntry:
    nutrition = calculate_entry(session, user, payload)
    return NutritionEntry.model_validate(
        {
            "owner_id": user.id,
            "log_date": payload.log_date,
            "meal_type": payload.meal_type,
            "note": payload.note,
            "source_type": payload.source_type,
            "recipe_id": nutrition.recipe_id,
            "product_id": nutrition.product_id,
            "ingredient_id": nutrition.ingredient_id,
            "title_snapshot": nutrition.title,
            "brand_snapshot": nutrition.brand,
            "quantity": payload.quantity,
            "unit": payload.unit,
            "calories": nutrition.calories,
            "carbohydrates": nutrition.carbohydrates,
            "fat": nutrition.fat,
            "protein": nutrition.protein,
        }
    )


def replace_entry(
    entry: NutritionEntry,
    session: Session,
    user: User,
    payload: NutritionEntryCreate,
) -> None:
    replacement = build_entry(session, user, payload)
    for field in (
        "log_date",
        "meal_type",
        "note",
        "source_type",
        "recipe_id",
        "product_id",
        "ingredient_id",
        "title_snapshot",
        "brand_snapshot",
        "quantity",
        "unit",
        "calories",
        "carbohydrates",
        "fat",
        "protein",
    ):
        setattr(entry, field, getattr(replacement, field))
    entry.updated_at = datetime.now(UTC)


def entry_to_public(
    entry: NutritionEntry,
    session: Session,
    user: User,
) -> NutritionEntryPublic:
    source_ids = {
        NutritionSourceType.RECIPE: entry.recipe_id,
        NutritionSourceType.PRODUCT: entry.product_id,
        NutritionSourceType.INGREDIENT: entry.ingredient_id,
        NutritionSourceType.MANUAL: None,
    }
    source_id = source_ids[entry.source_type]
    return NutritionEntryPublic(
        id=entry.id,
        owner_id=entry.owner_id,
        log_date=entry.log_date,
        meal_type=entry.meal_type,
        note=entry.note,
        source_type=entry.source_type,
        source_id=source_id,
        source_available=_source_is_available(entry, session, user),
        title=entry.title_snapshot,
        brand=entry.brand_snapshot,
        quantity=entry.quantity,
        unit=entry.unit,
        calories=entry.calories,
        carbohydrates=entry.carbohydrates,
        fat=entry.fat,
        protein=entry.protein,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def common_entries(
    session: Session,
    user: User,
    *,
    limit: int,
) -> NutritionCommonEntriesPublic:
    """Return repeatable entry variants derived from the caller's diary history."""
    history = session.exec(
        select(NutritionEntry)
        .where(NutritionEntry.owner_id == user.id)
        .order_by(col(NutritionEntry.created_at).desc(), col(NutritionEntry.id).desc())
    ).all()

    groups: dict[tuple[object, ...], _CommonEntryGroup] = {}
    for entry in history:
        key = _common_entry_key(entry)
        if key is None:
            continue
        group = groups.get(key)
        if group is None:
            groups[key] = _CommonEntryGroup(
                entry=entry,
                use_count=1,
                last_used_at=entry.created_at,
            )
            continue
        group.use_count += 1
        if entry.created_at > group.last_used_at:
            group.entry = entry
            group.last_used_at = entry.created_at

    ranked = sorted(
        (group for group in groups.values() if group.use_count >= 2),
        key=lambda group: (group.use_count, group.last_used_at),
        reverse=True,
    )
    items: list[NutritionCommonEntryPublic] = []
    for group in ranked:
        nutrition = _repeatable_nutrition(group.entry, session, user)
        if nutrition is None:
            continue
        entry = group.entry
        items.append(
            NutritionCommonEntryPublic(
                source_type=entry.source_type,
                source_id=_entry_source_id(entry),
                title=nutrition.title,
                brand=nutrition.brand,
                quantity=entry.quantity,
                unit=entry.unit,
                calories=nutrition.calories,
                carbohydrates=nutrition.carbohydrates,
                fat=nutrition.fat,
                protein=nutrition.protein,
                use_count=group.use_count,
                last_used_at=group.last_used_at,
            )
        )
        if len(items) == limit:
            break
    return NutritionCommonEntriesPublic(entries=items)


def _common_entry_key(entry: NutritionEntry) -> tuple[object, ...] | None:
    source_id = _entry_source_id(entry)
    shared = (entry.source_type, entry.quantity, entry.unit)
    if entry.source_type != NutritionSourceType.MANUAL:
        if source_id is None:
            return None
        return (*shared, source_id)
    return (
        *shared,
        " ".join(entry.title_snapshot.split()).casefold(),
        " ".join((entry.brand_snapshot or "").split()).casefold(),
        entry.calories,
        entry.carbohydrates,
        entry.fat,
        entry.protein,
    )


def _entry_source_id(entry: NutritionEntry) -> uuid.UUID | None:
    if entry.source_type == NutritionSourceType.RECIPE:
        return entry.recipe_id
    if entry.source_type == NutritionSourceType.PRODUCT:
        return entry.product_id
    if entry.source_type == NutritionSourceType.INGREDIENT:
        return entry.ingredient_id
    return None


def _repeatable_nutrition(
    entry: NutritionEntry,
    session: Session,
    user: User,
) -> CalculatedNutrition | None:
    if entry.source_type == NutritionSourceType.MANUAL:
        return CalculatedNutrition(
            title=entry.title_snapshot,
            brand=entry.brand_snapshot,
            calories=entry.calories,
            carbohydrates=entry.carbohydrates,
            fat=entry.fat,
            protein=entry.protein,
        )
    source_id = _entry_source_id(entry)
    if source_id is None:
        return None
    if entry.source_type == NutritionSourceType.RECIPE:
        payload: NutritionEntryCreate = RecipeNutritionEntryCreate(
            source_type="recipe",
            source_id=source_id,
            log_date=entry.log_date,
            meal_type=entry.meal_type,
            quantity=entry.quantity,
            unit=entry.unit,
        )
    elif entry.source_type == NutritionSourceType.PRODUCT:
        payload = ProductNutritionEntryCreate(
            source_type="product",
            source_id=source_id,
            log_date=entry.log_date,
            meal_type=entry.meal_type,
            quantity=entry.quantity,
            unit=entry.unit,
        )
    else:
        payload = IngredientNutritionEntryCreate(
            source_type="ingredient",
            source_id=source_id,
            log_date=entry.log_date,
            meal_type=entry.meal_type,
            quantity=entry.quantity,
            unit=entry.unit,
        )
    try:
        return calculate_entry(session, user, payload)
    except (NutritionInputError, NutritionSourceNotFoundError):
        return None


def _source_is_available(entry: NutritionEntry, session: Session, user: User) -> bool:
    if entry.source_type == NutritionSourceType.MANUAL:
        return True
    if entry.source_type == NutritionSourceType.RECIPE:
        if entry.recipe_id is None:
            return False
        recipe = session.get(Recipe, entry.recipe_id)
        return recipe is not None and can_view_recipe(session, recipe, user)
    if entry.source_type == NutritionSourceType.PRODUCT:
        if entry.product_id is None:
            return False
        product = session.get(Product, entry.product_id)
        return product is not None and product.owner_id == user.id
    if entry.ingredient_id is None:
        return False
    return session.get(Ingredient, entry.ingredient_id) is not None


def _calculate_recipe_entry(
    session: Session,
    user: User,
    payload: RecipeNutritionEntryCreate,
) -> CalculatedNutrition:
    if payload.unit != NutritionEntryUnit.SERVING:
        raise NutritionInputError("Recipes can only be logged in servings")
    recipe = session.get(Recipe, payload.source_id)
    if recipe is None or not can_view_recipe(session, recipe, user):
        raise NutritionSourceNotFoundError("Recipe not found")

    factor = payload.quantity / recipe.servings
    total = calculate_recipe_nutrients(session, recipe)
    return _checked_nutrition(
        title=recipe.title,
        brand=None,
        calories=total.calories * factor,
        carbohydrates=total.carbohydrates * factor,
        fat=total.fat * factor,
        protein=total.protein * factor,
        recipe_id=recipe.id,
    )


def _calculate_product_entry(
    session: Session,
    user: User,
    payload: ProductNutritionEntryCreate,
) -> CalculatedNutrition:
    product = session.get(Product, payload.source_id)
    if product is None or product.owner_id != user.id:
        raise NutritionSourceNotFoundError("Product not found")

    factor = _product_nutrition_factor(product, payload.quantity, payload.unit)
    return _checked_nutrition(
        title=product.title,
        brand=product.brand,
        calories=product.calories * factor,
        carbohydrates=_scale_optional(product.carbohydrates, factor),
        fat=_scale_optional(product.fat, factor),
        protein=_scale_optional(product.protein, factor),
        product_id=product.id,
    )


def _product_nutrition_factor(
    product: Product,
    quantity: float,
    unit: NutritionEntryUnit,
) -> float:
    basis = product.nutrition_basis
    if (
        basis == ProductNutritionBasis.PER_SERVING
        and unit == NutritionEntryUnit.SERVING
    ):
        return quantity
    if (
        basis == ProductNutritionBasis.PER_PACKAGE
        and unit == NutritionEntryUnit.PACKAGE
    ):
        return quantity

    physical_amount, physical_unit = _product_physical_amount(product, quantity, unit)
    if basis == ProductNutritionBasis.PER_100G:
        if physical_unit != "g":
            raise NutritionInputError("This product's nutrition is based on grams")
        return physical_amount / 100
    if basis == ProductNutritionBasis.PER_100ML:
        if physical_unit != "ml":
            raise NutritionInputError(
                "This product's nutrition is based on millilitres"
            )
        return physical_amount / 100
    if basis == ProductNutritionBasis.PER_SERVING:
        size, size_unit = _required_product_size(
            product.serving_size,
            product.serving_size_unit,
            "serving size",
        )
    else:
        size, size_unit = _required_product_size(
            product.package_size,
            product.package_size_unit,
            "package size",
        )
    if physical_unit != size_unit:
        raise NutritionInputError("Mass and volume cannot be converted without density")
    return physical_amount / size


def _product_physical_amount(
    product: Product,
    quantity: float,
    unit: NutritionEntryUnit,
) -> tuple[float, str]:
    if unit == NutritionEntryUnit.GRAM:
        return quantity, "g"
    if unit == NutritionEntryUnit.MILLILITER:
        return quantity, "ml"
    if unit == NutritionEntryUnit.SERVING:
        size, size_unit = _required_product_size(
            product.serving_size,
            product.serving_size_unit,
            "serving size",
        )
        return quantity * size, size_unit
    if unit == NutritionEntryUnit.PACKAGE:
        size, size_unit = _required_product_size(
            product.package_size,
            product.package_size_unit,
            "package size",
        )
        return quantity * size, size_unit
    raise NutritionInputError("Products cannot be logged in pieces")


def _required_product_size(
    amount: float | None,
    unit: object | None,
    label: str,
) -> tuple[float, str]:
    if amount is None or unit is None:
        raise NutritionInputError(f"This product does not have a {label}")
    return amount, str(unit)


def _calculate_ingredient_entry(
    session: Session,
    payload: IngredientNutritionEntryCreate,
) -> CalculatedNutrition:
    ingredient = session.get(Ingredient, payload.source_id)
    if ingredient is None:
        raise NutritionSourceNotFoundError("Ingredient not found")
    if payload.unit == NutritionEntryUnit.GRAM:
        grams = payload.quantity
    elif payload.unit == NutritionEntryUnit.PIECE:
        if ingredient.weight_per_piece <= 0:
            raise NutritionInputError("This ingredient has no usable piece weight")
        grams = payload.quantity * ingredient.weight_per_piece
    elif payload.unit == NutritionEntryUnit.MILLILITER:
        raise NutritionInputError(
            "Ingredients cannot be logged by volume without density"
        )
    else:
        raise NutritionInputError("Ingredients can only be logged in grams or pieces")

    factor = grams / 100
    return _checked_nutrition(
        title=ingredient.title,
        brand=None,
        calories=ingredient.calories * factor,
        carbohydrates=ingredient.carbohydrates * factor,
        fat=ingredient.fat * factor,
        protein=ingredient.protein * factor,
        ingredient_id=ingredient.id,
    )


def _calculate_manual_entry(
    payload: ManualNutritionEntryCreate,
) -> CalculatedNutrition:
    if payload.unit != NutritionEntryUnit.PIECE or payload.quantity != 1:
        raise NutritionInputError(
            "Manual nutrition values are totals and must use one piece"
        )
    return _checked_nutrition(
        title=payload.title,
        brand=payload.brand,
        calories=payload.calories,
        carbohydrates=payload.carbohydrates,
        fat=payload.fat,
        protein=payload.protein,
    )


def _scale_optional(value: float | None, factor: float) -> float | None:
    return None if value is None else value * factor


def _checked_nutrition(
    *,
    title: str,
    brand: str | None,
    calories: float,
    carbohydrates: float | None,
    fat: float | None,
    protein: float | None,
    recipe_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
    ingredient_id: uuid.UUID | None = None,
) -> CalculatedNutrition:
    for value in (calories, carbohydrates, fat, protein):
        if value is not None and not math.isfinite(float(value)):
            raise NutritionInputError("Calculated nutrition is too large")
    return CalculatedNutrition(
        title=title,
        brand=brand,
        calories=calories,
        carbohydrates=carbohydrates,
        fat=fat,
        protein=protein,
        recipe_id=recipe_id,
        product_id=product_id,
        ingredient_id=ingredient_id,
    )
