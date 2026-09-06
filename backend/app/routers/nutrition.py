from __future__ import annotations

import math
import uuid
from datetime import UTC, date, datetime

from fastapi import APIRouter, HTTPException, Query, Security, status
from pydantic import ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select

from app.deps import SessionDep, get_current_user
from app.models import (
    Ingredient,
    IngredientNutritionEntryCreate,
    ManualNutritionEntryCreate,
    NutritionCatalogIngredientPublic,
    NutritionCatalogPublic,
    NutritionCatalogRecipePublic,
    NutritionCommonEntriesPublic,
    NutritionDayPublic,
    NutritionEntriesBatchCreate,
    NutritionEntry,
    NutritionEntryBatchPublic,
    NutritionEntryCreate,
    NutritionEntryMoveUpdate,
    NutritionEntryPublic,
    NutritionMealGroupPublic,
    NutritionMealType,
    NutritionTotalsPublic,
    Product,
    ProductNutritionEntryCreate,
    ProductPublic,
    QuickAddCandidatePublic,
    QuickAddPreviewPublic,
    QuickAddPreviewRequest,
    QuickAddPreviewRowPublic,
    Recipe,
    RecipeNutritionEntryCreate,
    User,
)
from app.nutrition_service import (
    CalculatedNutrition,
    NutritionInputError,
    NutritionSourceNotFoundError,
    build_entry,
    calculate_entry,
    common_entries,
    entry_to_public,
    replace_entry,
)
from app.quick_add import (
    CatalogCandidate,
    FoodSourceType,
    ParseStatus,
    QuickAddDraft,
    parse_quick_add,
)
from app.recipe_service import (
    calculate_recipe_nutrients,
    calculate_recipe_weight_grams,
    visible_recipe_statement,
)

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


def _translate_nutrition_error(exc: Exception) -> HTTPException:
    if isinstance(exc, NutritionSourceNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=422, detail=str(exc))


def _commit_entries(session: SessionDep, entries: list[NutritionEntry]) -> None:
    session.add_all(entries)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="A food source changed while the entries were being saved",
        ) from exc
    for entry in entries:
        session.refresh(entry)


def _owned_entry(
    session: SessionDep, entry_id: uuid.UUID, current_user: User
) -> NutritionEntry:
    entry = session.exec(
        select(NutritionEntry).where(
            NutritionEntry.id == entry_id,
            NutritionEntry.owner_id == current_user.id,
        )
    ).first()
    if entry is None:
        raise HTTPException(status_code=404, detail="Nutrition entry not found")
    return entry


def _totals(entries: list[NutritionEntry]) -> NutritionTotalsPublic:
    carbohydrates_unknown = any(entry.carbohydrates is None for entry in entries)
    fat_unknown = any(entry.fat is None for entry in entries)
    protein_unknown = any(entry.protein is None for entry in entries)
    missing_nutrients = [
        name
        for name, is_unknown in (
            ("carbohydrates", carbohydrates_unknown),
            ("fat", fat_unknown),
            ("protein", protein_unknown),
        )
        if is_unknown
    ]
    try:
        calories = math.fsum(entry.calories for entry in entries)
        carbohydrates = math.fsum(entry.carbohydrates or 0 for entry in entries)
        fat = math.fsum(entry.fat or 0 for entry in entries)
        protein = math.fsum(entry.protein or 0 for entry in entries)
    except OverflowError as exc:
        raise HTTPException(
            status_code=422, detail="Nutrition totals exceed the supported range"
        ) from exc
    if not all(
        math.isfinite(value) for value in (calories, carbohydrates, fat, protein)
    ):
        raise HTTPException(
            status_code=422, detail="Nutrition totals exceed the supported range"
        )

    return NutritionTotalsPublic(
        calories=calories,
        carbohydrates=carbohydrates,
        fat=fat,
        protein=protein,
        carbohydrates_unknown=carbohydrates_unknown,
        fat_unknown=fat_unknown,
        protein_unknown=protein_unknown,
        incomplete_entry_count=sum(
            1
            for entry in entries
            if entry.carbohydrates is None or entry.fat is None or entry.protein is None
        ),
        missing_nutrients=missing_nutrients,
    )


def _day(session: SessionDep, current_user: User, log_date: date) -> NutritionDayPublic:
    entries = list(
        session.exec(
            select(NutritionEntry)
            .where(
                NutritionEntry.owner_id == current_user.id,
                NutritionEntry.log_date == log_date,
            )
            .order_by(col(NutritionEntry.created_at), col(NutritionEntry.id))
        ).all()
    )
    groups = []
    for meal_type in NutritionMealType:
        grouped_entries = [entry for entry in entries if entry.meal_type == meal_type]
        groups.append(
            NutritionMealGroupPublic(
                meal_type=meal_type,
                totals=_totals(grouped_entries),
                entries=[
                    entry_to_public(entry, session, current_user)
                    for entry in grouped_entries
                ],
            )
        )
    return NutritionDayPublic(log_date=log_date, totals=_totals(entries), groups=groups)


def _catalog(
    session: SessionDep,
    current_user: User,
    query: str | None,
    limit: int | None,
) -> NutritionCatalogPublic:
    search = query.strip() if query else ""

    recipe_statement = visible_recipe_statement(current_user)
    if search:
        recipe_statement = recipe_statement.where(
            col(Recipe.title).ilike(f"%{search}%")
        )
    recipe_statement = recipe_statement.order_by(col(Recipe.title))
    if limit is not None:
        recipe_statement = recipe_statement.limit(limit)
    recipes = session.exec(recipe_statement).all()
    recipe_items: list[NutritionCatalogRecipePublic] = []
    for recipe in recipes:
        nutrients = calculate_recipe_nutrients(session, recipe)
        factor = 1 / recipe.servings
        recipe_items.append(
            NutritionCatalogRecipePublic(
                id=recipe.id,
                title=recipe.title,
                servings=recipe.servings,
                serving_weight_grams=(
                    calculate_recipe_weight_grams(session, recipe) / recipe.servings
                ),
                calories=nutrients.calories * factor,
                carbohydrates=nutrients.carbohydrates * factor,
                fat=nutrients.fat * factor,
                protein=nutrients.protein * factor,
            )
        )

    product_statement = select(Product).where(Product.owner_id == current_user.id)
    if search:
        product_statement = product_statement.where(
            or_(
                col(Product.title).ilike(f"%{search}%"),
                col(Product.brand).ilike(f"%{search}%"),
                col(Product.barcode).ilike(f"%{search}%"),
            )
        )
    product_statement = product_statement.order_by(col(Product.title))
    if limit is not None:
        product_statement = product_statement.limit(limit)
    products = session.exec(product_statement).all()

    ingredient_statement = select(Ingredient)
    if search:
        ingredient_statement = ingredient_statement.where(
            col(Ingredient.title).ilike(f"%{search}%")
        )
    ingredient_statement = ingredient_statement.order_by(col(Ingredient.title))
    if limit is not None:
        ingredient_statement = ingredient_statement.limit(limit)
    ingredients = session.exec(ingredient_statement).all()

    return NutritionCatalogPublic(
        recipes=recipe_items,
        products=[ProductPublic.model_validate(product) for product in products],
        ingredients=[
            NutritionCatalogIngredientPublic(
                id=ingredient.id,
                title=ingredient.title,
                calories=ingredient.calories,
                carbohydrates=ingredient.carbohydrates,
                fat=ingredient.fat,
                protein=ingredient.protein,
                weight_per_piece=ingredient.weight_per_piece or None,
            )
            for ingredient in ingredients
        ],
    )


@router.get("/day/{log_date}", response_model=NutritionDayPublic)
def get_nutrition_day(
    session: SessionDep,
    log_date: date,
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    return _day(session, current_user, log_date)


@router.get("/catalog", response_model=NutritionCatalogPublic)
def get_nutrition_catalog(
    session: SessionDep,
    query: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    return _catalog(session, current_user, query, limit)


@router.get("/common-entries", response_model=NutritionCommonEntriesPublic)
def get_common_nutrition_entries(
    session: SessionDep,
    limit: int = Query(default=6, ge=1, le=20),
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    return common_entries(session, current_user, limit=limit)


@router.post(
    "/entries",
    response_model=NutritionEntryPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_nutrition_entry(
    session: SessionDep,
    entry_in: NutritionEntryCreate,
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    try:
        entry = build_entry(session, current_user, entry_in)
    except (NutritionInputError, NutritionSourceNotFoundError) as exc:
        raise _translate_nutrition_error(exc) from exc
    _commit_entries(session, [entry])
    return entry_to_public(entry, session, current_user)


@router.post(
    "/entries/batch",
    response_model=NutritionEntryBatchPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_nutrition_entries(
    session: SessionDep,
    batch_in: NutritionEntriesBatchCreate,
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    try:
        entries = [
            build_entry(session, current_user, entry_in)
            for entry_in in batch_in.entries
        ]
    except (NutritionInputError, NutritionSourceNotFoundError) as exc:
        session.rollback()
        raise _translate_nutrition_error(exc) from exc
    _commit_entries(session, entries)
    return NutritionEntryBatchPublic(
        entries=[entry_to_public(entry, session, current_user) for entry in entries]
    )


@router.patch("/entries/{entry_id}", response_model=NutritionEntryPublic)
def move_nutrition_entry(
    session: SessionDep,
    entry_id: uuid.UUID,
    entry_in: NutritionEntryMoveUpdate,
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    entry = _owned_entry(session, entry_id, current_user)
    updates = entry_in.model_dump(exclude_unset=True)
    if updates:
        entry.sqlmodel_update(updates)
        entry.updated_at = datetime.now(UTC)
        _commit_entries(session, [entry])
    return entry_to_public(entry, session, current_user)


@router.put("/entries/{entry_id}", response_model=NutritionEntryPublic)
def replace_nutrition_entry(
    session: SessionDep,
    entry_id: uuid.UUID,
    entry_in: NutritionEntryCreate,
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    entry = _owned_entry(session, entry_id, current_user)
    try:
        replace_entry(entry, session, current_user, entry_in)
    except (NutritionInputError, NutritionSourceNotFoundError) as exc:
        raise _translate_nutrition_error(exc) from exc
    _commit_entries(session, [entry])
    return entry_to_public(entry, session, current_user)


@router.delete("/entries/{entry_id}", response_model=NutritionEntryPublic)
def delete_nutrition_entry(
    session: SessionDep,
    entry_id: uuid.UUID,
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    entry = _owned_entry(session, entry_id, current_user)
    response = entry_to_public(entry, session, current_user)
    session.delete(entry)
    session.commit()
    return response


def _quick_add_candidates(catalog: NutritionCatalogPublic) -> list[CatalogCandidate]:
    candidates: list[CatalogCandidate] = []

    def add_candidate(
        candidate_id: uuid.UUID,
        source_type: FoodSourceType,
        title: str,
        aliases: tuple[str, ...] = (),
    ) -> None:
        try:
            candidates.append(
                CatalogCandidate(str(candidate_id), source_type, title, aliases)
            )
        except ValueError:
            # Legacy recipe and ingredient titles predate parser-safe validation.
            # One unusable catalog row must not break previewing every other food.
            return

    for recipe in catalog.recipes:
        add_candidate(recipe.id, FoodSourceType.RECIPE, recipe.title)
    for product in catalog.products:
        add_candidate(
            product.id,
            FoodSourceType.PRODUCT,
            product.title,
            tuple(
                value
                for value in (
                    product.barcode,
                    f"{product.brand} {product.title}" if product.brand else None,
                )
                if value
            ),
        )
    for ingredient in catalog.ingredients:
        add_candidate(
            ingredient.id,
            FoodSourceType.INGREDIENT,
            ingredient.title,
        )
    return candidates


def _draft_payload(
    draft: QuickAddDraft, request: QuickAddPreviewRequest
) -> NutritionEntryCreate | None:
    if draft.status is not ParseStatus.RESOLVED:
        return None
    if draft.source_type is FoodSourceType.MANUAL:
        nutrition = draft.manual_nutrition
        if nutrition is None or draft.name is None:
            return None
        return ManualNutritionEntryCreate(
            source_type="manual",
            log_date=request.log_date,
            meal_type=draft.meal_group.value,
            quantity=1,
            unit="piece",
            title=draft.name,
            calories=float(nutrition.calories),
            carbohydrates=(
                float(nutrition.carbohydrates)
                if nutrition.carbohydrates is not None
                else None
            ),
            fat=float(nutrition.fat) if nutrition.fat is not None else None,
            protein=(
                float(nutrition.protein) if nutrition.protein is not None else None
            ),
        )
    if draft.resolved_candidate is None or draft.quantity is None or draft.unit is None:
        return None
    source_id = uuid.UUID(draft.resolved_candidate.id)
    quantity = float(draft.quantity)
    unit = draft.unit.value
    if draft.source_type is FoodSourceType.RECIPE:
        return RecipeNutritionEntryCreate(
            source_type="recipe",
            source_id=source_id,
            log_date=request.log_date,
            meal_type=draft.meal_group.value,
            quantity=quantity,
            unit=unit,
        )
    if draft.source_type is FoodSourceType.PRODUCT:
        return ProductNutritionEntryCreate(
            source_type="product",
            source_id=source_id,
            log_date=request.log_date,
            meal_type=draft.meal_group.value,
            quantity=quantity,
            unit=unit,
        )
    if draft.source_type is FoodSourceType.INGREDIENT:
        return IngredientNutritionEntryCreate(
            source_type="ingredient",
            source_id=source_id,
            log_date=request.log_date,
            meal_type=draft.meal_group.value,
            quantity=quantity,
            unit=unit,
        )
    return None


def _candidate_public(draft: QuickAddDraft) -> list[QuickAddCandidatePublic]:
    exact = [
        QuickAddCandidatePublic(
            source_type=candidate.source_type.value,
            source_id=uuid.UUID(candidate.id),
            title=candidate.title,
        )
        for candidate in draft.exact_matches
    ]
    suggestions = [
        QuickAddCandidatePublic(
            source_type=suggestion.candidate.source_type.value,
            source_id=uuid.UUID(suggestion.candidate.id),
            title=suggestion.candidate.title,
            similarity=suggestion.similarity,
        )
        for suggestion in draft.suggestions
    ]
    return exact + suggestions


def _preview_row(
    session: SessionDep,
    current_user: User,
    request: QuickAddPreviewRequest,
    draft: QuickAddDraft,
) -> QuickAddPreviewRowPublic:
    source_id = (
        uuid.UUID(draft.resolved_candidate.id)
        if draft.resolved_candidate is not None
        else None
    )
    status_value = draft.status.value
    error_code = draft.error_code
    message = draft.message
    calculated: CalculatedNutrition | None = None
    try:
        payload = _draft_payload(draft, request)
    except (ValidationError, OverflowError):
        payload = None
        status_value = ParseStatus.INVALID.value
        error_code = "value_out_of_range"
        message = "The parsed entry contains a value outside the supported range."
    if payload is not None:
        try:
            calculated = calculate_entry(session, current_user, payload)
        except (NutritionInputError, NutritionSourceNotFoundError) as exc:
            status_value = ParseStatus.INVALID.value
            error_code = "invalid_source_quantity"
            message = str(exc)

    return QuickAddPreviewRowPublic(
        line_number=draft.line_number,
        original_text=draft.original_text,
        meal_type=draft.meal_group.value,
        status=status_value,
        source_type=draft.source_type.value if draft.source_type else None,
        source_id=source_id,
        title=calculated.title if calculated else draft.name,
        quantity=float(draft.quantity) if draft.quantity is not None else None,
        unit=draft.unit.value if draft.unit else None,
        calories=calculated.calories if calculated else None,
        carbohydrates=calculated.carbohydrates if calculated else None,
        fat=calculated.fat if calculated else None,
        protein=calculated.protein if calculated else None,
        candidates=_candidate_public(draft),
        error_code=error_code,
        message=message,
    )


@router.post("/quick-add/preview", response_model=QuickAddPreviewPublic)
def preview_quick_add(
    session: SessionDep,
    preview_in: QuickAddPreviewRequest,
    current_user: User = Security(get_current_user, scopes=["nutrition:use"]),
):
    catalog = _catalog(session, current_user, None, None)
    result = parse_quick_add(
        preview_in.text,
        _quick_add_candidates(catalog),
        preview_in.default_meal.value,
    )
    rows = [
        _preview_row(session, current_user, preview_in, draft)
        for draft in result.drafts
    ]
    return QuickAddPreviewPublic(
        rows=rows,
        can_confirm=bool(rows)
        and all(row.status == ParseStatus.RESOLVED.value for row in rows),
    )
