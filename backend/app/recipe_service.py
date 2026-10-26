from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import or_
from sqlmodel import Session, col, select

from app.models import Ingredient, Recipe, RecipeViewerLink, User
from app.permissions import get_user_effective_scopes


@dataclass(frozen=True, slots=True)
class RecipeNutrients:
    calories: float
    carbohydrates: float
    fat: float
    protein: float

    def scaled(self, factor: float) -> RecipeNutrients:
        return RecipeNutrients(
            calories=self.calories * factor,
            carbohydrates=self.carbohydrates * factor,
            fat=self.fat * factor,
            protein=self.protein * factor,
        )

    def plus(self, other: RecipeNutrients) -> RecipeNutrients:
        return RecipeNutrients(
            calories=self.calories + other.calories,
            carbohydrates=self.carbohydrates + other.carbohydrates,
            fat=self.fat + other.fat,
            protein=self.protein + other.protein,
        )


def can_view_all_hidden_recipes(user: User | None) -> bool:
    if user is None:
        return False
    return user.is_superuser or "recipes:read_hidden" in get_user_effective_scopes(user)


def can_view_recipe(session: Session, recipe: Recipe, user: User | None) -> bool:
    if not recipe.is_hidden:
        return True
    if user is None:
        return False
    if recipe.owner_id == user.id or can_view_all_hidden_recipes(user):
        return True
    return (
        session.exec(
            select(RecipeViewerLink).where(
                RecipeViewerLink.recipe_id == recipe.id,
                RecipeViewerLink.user_id == user.id,
            )
        ).first()
        is not None
    )


def visible_recipe_statement(user: User):
    statement = select(Recipe)
    if can_view_all_hidden_recipes(user):
        return statement
    viewer_subquery = select(RecipeViewerLink.recipe_id).where(
        RecipeViewerLink.user_id == user.id
    )
    return statement.where(
        or_(
            col(Recipe.is_hidden).is_(False),
            col(Recipe.owner_id) == user.id,
            col(Recipe.id).in_(viewer_subquery),
        )
    )


def calculate_recipe_nutrients(session: Session, recipe: Recipe) -> RecipeNutrients:
    """Return full-recipe nutrient totals without display rounding."""
    return _calculate_recipe_nutrients(session, recipe, 1.0, {recipe.id})


def calculate_recipe_weight_grams(session: Session, recipe: Recipe) -> float:
    """Return the consumed recipe weight using the app's existing gram convention."""
    return _calculate_recipe_weight_grams(session, recipe, 1.0, {recipe.id})


def _calculate_recipe_weight_grams(
    session: Session,
    recipe: Recipe,
    scale: float,
    stack: set[uuid.UUID],
) -> float:
    total = 0.0
    for link in recipe.ingredient_links:
        ingredient: Ingredient | None = link.ingredient
        if ingredient is None:
            continue
        amount = link.amount if link.consumed_amount is None else link.consumed_amount
        if link.unit in {"kg", "L"}:
            grams = amount * 1000
        elif link.unit == "pcs":
            grams = amount * ingredient.weight_per_piece
        else:
            # Preserve the recipe system's existing 1 ml == 1 g convention.
            grams = amount
        total += grams * scale

    for link in recipe.sub_recipe_links:
        sub_recipe_id = link.sub_recipe_id
        if sub_recipe_id is None or sub_recipe_id in stack:
            continue
        sub_recipe = session.get(Recipe, sub_recipe_id)
        if sub_recipe is None:
            continue
        stack.add(sub_recipe_id)
        total += _calculate_recipe_weight_grams(
            session,
            sub_recipe,
            scale * link.scale_factor,
            stack,
        )
        stack.remove(sub_recipe_id)

    return total


def _calculate_recipe_nutrients(
    session: Session,
    recipe: Recipe,
    scale: float,
    stack: set[uuid.UUID],
) -> RecipeNutrients:
    total = RecipeNutrients(0.0, 0.0, 0.0, 0.0)

    for link in recipe.ingredient_links:
        ingredient: Ingredient | None = link.ingredient
        if ingredient is None:
            continue
        amount = link.amount if link.consumed_amount is None else link.consumed_amount
        amount *= scale
        if link.unit == "kg":
            grams = amount * 1000
        elif link.unit == "L":
            # Preserve the recipe system's existing 1 ml == 1 g convention.
            grams = amount * 1000
        elif link.unit == "pcs":
            grams = amount * ingredient.weight_per_piece
        else:
            grams = amount
        total = total.plus(
            RecipeNutrients(
                calories=ingredient.calories * grams / 100,
                carbohydrates=ingredient.carbohydrates * grams / 100,
                fat=ingredient.fat * grams / 100,
                protein=ingredient.protein * grams / 100,
            )
        )

    for link in recipe.sub_recipe_links:
        sub_recipe_id = link.sub_recipe_id
        if sub_recipe_id is None or sub_recipe_id in stack:
            continue
        sub_recipe = session.get(Recipe, sub_recipe_id)
        if sub_recipe is None:
            continue
        stack.add(sub_recipe_id)
        total = total.plus(
            _calculate_recipe_nutrients(
                session,
                sub_recipe,
                scale * link.scale_factor,
                stack,
            )
        )
        stack.remove(sub_recipe_id)

    return total
