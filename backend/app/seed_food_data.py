from __future__ import annotations

from typing import TypedDict

from sqlmodel import Session, select

from app.config import settings
from app.db import init_db
from app.models import Ingredient, Recipe, RecipeIngredientLink, User


class IngredientSeed(TypedDict):
    title: str
    calories: int
    carbohydrates: float
    fat: float
    protein: float
    weight_per_piece: int


class RecipeIngredientSeed(TypedDict):
    ingredient_title: str
    amount: float
    unit: str


class RecipeSeed(TypedDict):
    title: str
    instructions: str
    servings: int
    ingredients: list[RecipeIngredientSeed]
    image: str | None


INGREDIENT_SEEDS: list[IngredientSeed] = [
    {
        "title": "Rolled Oats",
        "calories": 389,
        "carbohydrates": 66.3,
        "fat": 6.9,
        "protein": 16.9,
        "weight_per_piece": 100,
    },
    {
        "title": "Greek Yogurt 2%",
        "calories": 73,
        "carbohydrates": 3.9,
        "fat": 2.0,
        "protein": 9.9,
        "weight_per_piece": 100,
    },
    {
        "title": "Banana",
        "calories": 89,
        "carbohydrates": 22.8,
        "fat": 0.3,
        "protein": 1.1,
        "weight_per_piece": 120,
    },
    {
        "title": "Blueberries",
        "calories": 57,
        "carbohydrates": 14.5,
        "fat": 0.3,
        "protein": 0.7,
        "weight_per_piece": 100,
    },
    {
        "title": "Chia Seeds",
        "calories": 486,
        "carbohydrates": 42.1,
        "fat": 30.7,
        "protein": 16.5,
        "weight_per_piece": 100,
    },
    {
        "title": "Honey",
        "calories": 304,
        "carbohydrates": 82.4,
        "fat": 0.0,
        "protein": 0.0,
        "weight_per_piece": 100,
    },
    {
        "title": "Whole Milk",
        "calories": 61,
        "carbohydrates": 4.8,
        "fat": 3.3,
        "protein": 3.2,
        "weight_per_piece": 100,
    },
    {
        "title": "Chicken Breast",
        "calories": 165,
        "carbohydrates": 0.0,
        "fat": 3.6,
        "protein": 31.0,
        "weight_per_piece": 170,
    },
    {
        "title": "Cooked Rice",
        "calories": 130,
        "carbohydrates": 28.2,
        "fat": 0.3,
        "protein": 2.7,
        "weight_per_piece": 100,
    },
    {
        "title": "Broccoli",
        "calories": 34,
        "carbohydrates": 6.6,
        "fat": 0.4,
        "protein": 2.8,
        "weight_per_piece": 250,
    },
    {
        "title": "Avocado",
        "calories": 160,
        "carbohydrates": 8.5,
        "fat": 14.7,
        "protein": 2.0,
        "weight_per_piece": 200,
    },
    {
        "title": "Olive Oil",
        "calories": 884,
        "carbohydrates": 0.0,
        "fat": 100.0,
        "protein": 0.0,
        "weight_per_piece": 100,
    },
    {
        "title": "Soy Sauce",
        "calories": 53,
        "carbohydrates": 4.9,
        "fat": 0.6,
        "protein": 8.1,
        "weight_per_piece": 100,
    },
    {
        "title": "Salmon Fillet",
        "calories": 208,
        "carbohydrates": 0.0,
        "fat": 13.0,
        "protein": 20.0,
        "weight_per_piece": 200,
    },
    {
        "title": "Whole Wheat Pasta",
        "calories": 348,
        "carbohydrates": 72.0,
        "fat": 2.2,
        "protein": 13.0,
        "weight_per_piece": 100,
    },
    {
        "title": "Parmesan",
        "calories": 431,
        "carbohydrates": 4.1,
        "fat": 29.0,
        "protein": 38.0,
        "weight_per_piece": 100,
    },
    {
        "title": "Spinach",
        "calories": 23,
        "carbohydrates": 3.6,
        "fat": 0.4,
        "protein": 2.9,
        "weight_per_piece": 100,
    },
    {
        "title": "Cherry Tomato",
        "calories": 18,
        "carbohydrates": 3.9,
        "fat": 0.2,
        "protein": 0.9,
        "weight_per_piece": 17,
    },
    {
        "title": "Garlic",
        "calories": 149,
        "carbohydrates": 33.1,
        "fat": 0.5,
        "protein": 6.4,
        "weight_per_piece": 5,
    },
    {
        "title": "Ground Turkey 93/7",
        "calories": 176,
        "carbohydrates": 0.0,
        "fat": 10.1,
        "protein": 20.5,
        "weight_per_piece": 100,
    },
    {
        "title": "Kidney Beans (Cooked)",
        "calories": 127,
        "carbohydrates": 22.8,
        "fat": 0.5,
        "protein": 8.7,
        "weight_per_piece": 100,
    },
    {
        "title": "Black Beans (Cooked)",
        "calories": 132,
        "carbohydrates": 23.7,
        "fat": 0.5,
        "protein": 8.9,
        "weight_per_piece": 100,
    },
    {
        "title": "Onion",
        "calories": 40,
        "carbohydrates": 9.3,
        "fat": 0.1,
        "protein": 1.1,
        "weight_per_piece": 110,
    },
    {
        "title": "Red Bell Pepper",
        "calories": 31,
        "carbohydrates": 6.0,
        "fat": 0.3,
        "protein": 1.0,
        "weight_per_piece": 120,
    },
    {
        "title": "Cottage Cheese (Low Fat)",
        "calories": 98,
        "carbohydrates": 3.4,
        "fat": 4.3,
        "protein": 11.1,
        "weight_per_piece": 100,
    },
    {
        "title": "Egg",
        "calories": 143,
        "carbohydrates": 0.7,
        "fat": 9.5,
        "protein": 12.6,
        "weight_per_piece": 50,
    },
]


RECIPE_SEEDS: list[RecipeSeed] = [
    {
        "title": "Overnight Oats Protein Jar",
        "servings": 2,
        "image": None,
        "instructions": (
            "<ol>"
            "<li>Mix oats, yogurt, milk, chia seeds, and honey in a bowl.</li>"
            "<li>Fold in blueberries and sliced banana.</li>"
            "<li>Cover and chill overnight.</li>"
            "<li>Stir and serve cold.</li>"
            "</ol>"
        ),
        "ingredients": [
            {"ingredient_title": "Rolled Oats", "amount": 80, "unit": "g"},
            {"ingredient_title": "Greek Yogurt 2%", "amount": 170, "unit": "g"},
            {"ingredient_title": "Whole Milk", "amount": 120, "unit": "ml"},
            {"ingredient_title": "Banana", "amount": 1, "unit": "pcs"},
            {"ingredient_title": "Blueberries", "amount": 80, "unit": "g"},
            {"ingredient_title": "Chia Seeds", "amount": 15, "unit": "g"},
            {"ingredient_title": "Honey", "amount": 10, "unit": "g"},
        ],
    },
    {
        "title": "Chicken Rice Power Bowl",
        "servings": 3,
        "image": None,
        "instructions": (
            "<ol>"
            "<li>Cook chicken breast in a pan until fully done.</li>"
            "<li>Steam broccoli until tender-crisp.</li>"
            "<li>Assemble bowls with rice, chicken, and broccoli.</li>"
            "<li>Top with avocado slices and drizzle soy sauce.</li>"
            "</ol>"
        ),
        "ingredients": [
            {"ingredient_title": "Chicken Breast", "amount": 350, "unit": "g"},
            {"ingredient_title": "Cooked Rice", "amount": 300, "unit": "g"},
            {"ingredient_title": "Broccoli", "amount": 220, "unit": "g"},
            {"ingredient_title": "Avocado", "amount": 0.5, "unit": "pcs"},
            {"ingredient_title": "Olive Oil", "amount": 15, "unit": "g"},
            {"ingredient_title": "Soy Sauce", "amount": 20, "unit": "ml"},
        ],
    },
    {
        "title": "Salmon Pasta",
        "servings": 4,
        "image": None,
        "instructions": (
            "<ol>"
            "<li>Cook pasta according to package instructions.</li>"
            "<li>Pan-sear salmon with olive oil until just cooked.</li>"
            "<li>Saute garlic, spinach, and tomatoes in the same pan.</li>"
            "<li>Toss everything together and finish with parmesan.</li>"
            "</ol>"
        ),
        "ingredients": [
            {"ingredient_title": "Whole Wheat Pasta", "amount": 250, "unit": "g"},
            {"ingredient_title": "Salmon Fillet", "amount": 300, "unit": "g"},
            {"ingredient_title": "Cherry Tomato", "amount": 250, "unit": "g"},
            {"ingredient_title": "Spinach", "amount": 120, "unit": "g"},
            {"ingredient_title": "Garlic", "amount": 3, "unit": "pcs"},
            {"ingredient_title": "Olive Oil", "amount": 12, "unit": "g"},
            {"ingredient_title": "Parmesan", "amount": 35, "unit": "g"},
        ],
    },
    {
        "title": "Turkey Bean Chili",
        "servings": 6,
        "image": None,
        "instructions": (
            "<ol>"
            "<li>Brown turkey with olive oil in a large pot.</li>"
            "<li>Add onion, garlic, and bell pepper and cook until soft.</li>"
            "<li>Add tomatoes and beans, then simmer for 25 minutes.</li>"
            "<li>Serve hot.</li>"
            "</ol>"
        ),
        "ingredients": [
            {"ingredient_title": "Ground Turkey 93/7", "amount": 500, "unit": "g"},
            {"ingredient_title": "Kidney Beans (Cooked)", "amount": 250, "unit": "g"},
            {"ingredient_title": "Black Beans (Cooked)", "amount": 250, "unit": "g"},
            {"ingredient_title": "Cherry Tomato", "amount": 500, "unit": "g"},
            {"ingredient_title": "Onion", "amount": 1, "unit": "pcs"},
            {"ingredient_title": "Red Bell Pepper", "amount": 1, "unit": "pcs"},
            {"ingredient_title": "Garlic", "amount": 2, "unit": "pcs"},
            {"ingredient_title": "Olive Oil", "amount": 15, "unit": "g"},
        ],
    },
    {
        "title": "Banana Protein Pancakes",
        "servings": 2,
        "image": None,
        "instructions": (
            "<ol>"
            "<li>Blend oats, cottage cheese, eggs, banana, and milk.</li>"
            "<li>Cook small pancakes on a non-stick pan.</li>"
            "<li>Serve with a light drizzle of honey.</li>"
            "</ol>"
        ),
        "ingredients": [
            {"ingredient_title": "Rolled Oats", "amount": 90, "unit": "g"},
            {
                "ingredient_title": "Cottage Cheese (Low Fat)",
                "amount": 200,
                "unit": "g",
            },
            {"ingredient_title": "Egg", "amount": 2, "unit": "pcs"},
            {"ingredient_title": "Banana", "amount": 1, "unit": "pcs"},
            {"ingredient_title": "Whole Milk", "amount": 80, "unit": "ml"},
            {"ingredient_title": "Honey", "amount": 12, "unit": "g"},
        ],
    },
]


def seed_ingredients(
    session: Session, *, overwrite_existing: bool = True
) -> tuple[int, int, int]:
    created = 0
    updated = 0
    skipped = 0

    for data in INGREDIENT_SEEDS:
        existing = session.exec(
            select(Ingredient).where(Ingredient.title == data["title"])
        ).first()

        if existing:
            if overwrite_existing:
                existing.calories = data["calories"]
                existing.carbohydrates = data["carbohydrates"]
                existing.fat = data["fat"]
                existing.protein = data["protein"]
                existing.weight_per_piece = data["weight_per_piece"]
                session.add(existing)
                updated += 1
            else:
                skipped += 1
            continue

        ingredient = Ingredient(**data)
        session.add(ingredient)
        created += 1

    session.commit()
    return created, updated, skipped


def _resolve_owner(session: Session, owner_email: str | None) -> User:
    init_db(session)
    target_email = owner_email or settings.FIRST_SUPERUSER
    owner = session.exec(select(User).where(User.email == target_email)).first()
    if not owner:
        raise ValueError(f"Could not find owner user with email '{target_email}'")
    return owner


def seed_recipes(
    session: Session,
    *,
    owner_email: str | None = None,
    overwrite_existing: bool = True,
    ensure_ingredients: bool = True,
) -> tuple[int, int, int]:
    if ensure_ingredients:
        seed_ingredients(session, overwrite_existing=False)

    owner = _resolve_owner(session, owner_email)

    ingredient_map = {
        ingredient.title: ingredient
        for ingredient in session.exec(select(Ingredient)).all()
    }

    missing_ingredients = sorted(
        {
            item["ingredient_title"]
            for recipe in RECIPE_SEEDS
            for item in recipe["ingredients"]
            if item["ingredient_title"] not in ingredient_map
        }
    )
    if missing_ingredients:
        missing_text = ", ".join(missing_ingredients)
        raise ValueError(
            "Cannot seed recipes. Missing ingredients: "
            f"{missing_text}. Run init-ingredients first."
        )

    created = 0
    updated = 0
    skipped = 0

    for data in RECIPE_SEEDS:
        existing = session.exec(
            select(Recipe).where(
                Recipe.title == data["title"], Recipe.owner_id == owner.id
            )
        ).first()

        if existing and not overwrite_existing:
            skipped += 1
            continue

        if existing:
            existing.instructions = data["instructions"]
            existing.servings = data["servings"]
            existing.image = data["image"]
            session.add(existing)
            session.flush()

            existing_links = session.exec(
                select(RecipeIngredientLink).where(
                    RecipeIngredientLink.recipe_id == existing.id
                )
            ).all()
            for link in existing_links:
                session.delete(link)
            # Ensure old link rows are removed before we insert replacements.
            session.flush()
            recipe_obj = existing
            updated += 1
        else:
            recipe_obj = Recipe(
                title=data["title"],
                instructions=data["instructions"],
                servings=data["servings"],
                image=data["image"],
                owner_id=owner.id,
            )
            session.add(recipe_obj)
            session.flush()
            created += 1

        for ingredient_item in data["ingredients"]:
            ingredient = ingredient_map[ingredient_item["ingredient_title"]]
            link = RecipeIngredientLink(
                recipe_id=recipe_obj.id,
                ingredient_id=ingredient.id,
                amount=ingredient_item["amount"],
                unit=ingredient_item["unit"],
            )
            session.add(link)

    session.commit()
    return created, updated, skipped
