import uuid
from fastapi import APIRouter, UploadFile, File
from fastapi import HTTPException, Security
from sqlmodel import select, desc
from sqlalchemy import or_
import cloudinary
import cloudinary.uploader
from app.config import get_settings
from app.deps import SessionDep, get_current_user, get_current_user_optional
from app.models import (
    Recipe,
    RecipeCreate,
    RecipeIngredientLink,
    RecipeIngredientSourcePublic,
    RecipeIngredientTotalPublic,
    RecipeSubRecipeLink,
    RecipePublic,
    RecipeViewerLink,
    Ingredient,
    User,
)
from app.permissions import get_user_effective_scopes


router = APIRouter(prefix="/recipes", tags=["recipes"])


def _validate_unique_sub_recipe_ids(recipe_in: RecipeCreate) -> None:
    sub_recipe_ids = [link.sub_recipe_id for link in recipe_in.sub_recipes]
    if len(sub_recipe_ids) != len(set(sub_recipe_ids)):
        raise HTTPException(
            status_code=400,
            detail="Each sub-recipe can only appear once in a recipe",
        )


def _validate_sub_recipes_exist(
    session: SessionDep,
    recipe_in: RecipeCreate,
    parent_recipe_id: uuid.UUID | None = None,
) -> None:
    for sub_recipe_link in recipe_in.sub_recipes:
        if parent_recipe_id and sub_recipe_link.sub_recipe_id == parent_recipe_id:
            raise HTTPException(
                status_code=400,
                detail="A recipe can not reference itself as a sub-recipe",
            )

        if not session.get(Recipe, sub_recipe_link.sub_recipe_id):
            raise HTTPException(
                status_code=404,
                detail=f"Sub-recipe not found: {sub_recipe_link.sub_recipe_id}",
            )


def _build_recipe_graph(
    session: SessionDep, excluded_parent_recipe_id: uuid.UUID | None = None
) -> dict[uuid.UUID, set[uuid.UUID]]:
    links = session.exec(select(RecipeSubRecipeLink)).all()
    graph: dict[uuid.UUID, set[uuid.UUID]] = {}

    for link in links:
        if (
            excluded_parent_recipe_id
            and link.parent_recipe_id == excluded_parent_recipe_id
        ):
            continue
        if not link.parent_recipe_id or not link.sub_recipe_id:
            continue
        graph.setdefault(link.parent_recipe_id, set()).add(link.sub_recipe_id)

    return graph


def _path_exists(
    graph: dict[uuid.UUID, set[uuid.UUID]], start: uuid.UUID, target: uuid.UUID
) -> bool:
    to_visit = [start]
    visited: set[uuid.UUID] = set()

    while to_visit:
        node = to_visit.pop()
        if node == target:
            return True
        if node in visited:
            continue
        visited.add(node)
        to_visit.extend(graph.get(node, set()))
    return False


def _validate_no_sub_recipe_cycles(
    session: SessionDep, parent_recipe_id: uuid.UUID, sub_recipe_ids: list[uuid.UUID]
) -> None:
    graph = _build_recipe_graph(session, excluded_parent_recipe_id=parent_recipe_id)

    for sub_recipe_id in sub_recipe_ids:
        if sub_recipe_id == parent_recipe_id:
            raise HTTPException(
                status_code=400,
                detail="A recipe can not reference itself as a sub-recipe",
            )
        if _path_exists(graph, sub_recipe_id, parent_recipe_id):
            raise HTTPException(
                status_code=400,
                detail="Sub-recipe linkage creates a cycle",
            )
        graph.setdefault(parent_recipe_id, set()).add(sub_recipe_id)


def _normalize_total_amount(amount: float, unit: str) -> tuple[float, str]:
    if unit == "kg":
        return amount * 1000, "g"
    if unit == "L":
        return amount * 1000, "ml"
    return amount, unit


def _to_grams(amount: float, unit: str, ingredient: Ingredient) -> float:
    if unit == "pcs":
        return amount * ingredient.weight_per_piece
    # Keep a 1:1 conversion for g/ml in current nutrition model.
    return amount


def _add_ingredient_total(
    totals: dict[tuple[uuid.UUID, str], RecipeIngredientTotalPublic],
    source_totals: dict[
        tuple[uuid.UUID, str], dict[uuid.UUID, RecipeIngredientSourcePublic]
    ],
    ingredient: Ingredient,
    amount: float,
    unit: str,
    source_recipe: Recipe,
    is_main_recipe: bool,
) -> None:
    normalized_amount, normalized_unit = _normalize_total_amount(amount, unit)
    grams_contribution = _to_grams(normalized_amount, normalized_unit, ingredient)
    calories_contribution = (ingredient.calories * grams_contribution) / 100
    carbohydrates_contribution = (ingredient.carbohydrates * grams_contribution) / 100
    fat_contribution = (ingredient.fat * grams_contribution) / 100
    protein_contribution = (ingredient.protein * grams_contribution) / 100

    key = (ingredient.id, normalized_unit)
    existing = totals.get(key)
    if existing:
        existing.amount += normalized_amount
        existing.grams += grams_contribution
        existing.calories += calories_contribution
        existing.carbohydrates += carbohydrates_contribution
        existing.fat += fat_contribution
        existing.protein += protein_contribution
    else:
        totals[key] = RecipeIngredientTotalPublic(
            ingredient_id=ingredient.id,
            title=ingredient.title,
            amount=normalized_amount,
            unit=normalized_unit,
            grams=grams_contribution,
            calories=calories_contribution,
            carbohydrates=carbohydrates_contribution,
            fat=fat_contribution,
            protein=protein_contribution,
            sources=[],
        )

    per_ingredient_sources = source_totals.setdefault(key, {})
    existing_source = per_ingredient_sources.get(source_recipe.id)
    if existing_source:
        existing_source.amount += normalized_amount
        return

    per_ingredient_sources[source_recipe.id] = RecipeIngredientSourcePublic(
        recipe_id=source_recipe.id,
        recipe_title=source_recipe.title,
        amount=normalized_amount,
        unit=normalized_unit,
        is_main_recipe=is_main_recipe,
    )


def _collect_total_ingredients(
    session: SessionDep,
    recipe: Recipe,
    scale: float,
    root_recipe_id: uuid.UUID,
    totals: dict[tuple[uuid.UUID, str], RecipeIngredientTotalPublic],
    source_totals: dict[
        tuple[uuid.UUID, str], dict[uuid.UUID, RecipeIngredientSourcePublic]
    ],
    stack: set[uuid.UUID],
) -> None:
    for ingredient_link in recipe.ingredient_links:
        ingredient = ingredient_link.ingredient
        if not ingredient:
            continue
        _add_ingredient_total(
            totals,
            source_totals,
            ingredient,
            ingredient_link.amount * scale,
            ingredient_link.unit,
            source_recipe=recipe,
            is_main_recipe=recipe.id == root_recipe_id,
        )

    for sub_recipe_link in recipe.sub_recipe_links:
        sub_recipe_id = sub_recipe_link.sub_recipe_id
        if not sub_recipe_id or sub_recipe_id in stack:
            continue

        sub_recipe = session.get(Recipe, sub_recipe_id)
        if not sub_recipe:
            continue

        stack.add(sub_recipe_id)
        _collect_total_ingredients(
            session,
            sub_recipe,
            scale * sub_recipe_link.scale_factor,
            root_recipe_id,
            totals,
            source_totals,
            stack,
        )
        stack.remove(sub_recipe_id)


def _calculate_total_ingredients(
    session: SessionDep, recipe: Recipe
) -> list[RecipeIngredientTotalPublic]:
    totals: dict[tuple[uuid.UUID, str], RecipeIngredientTotalPublic] = {}
    source_totals: dict[
        tuple[uuid.UUID, str], dict[uuid.UUID, RecipeIngredientSourcePublic]
    ] = {}
    _collect_total_ingredients(
        session,
        recipe,
        1.0,
        recipe.id,
        totals,
        source_totals,
        {recipe.id},
    )

    result: list[RecipeIngredientTotalPublic] = []
    for key, item in totals.items():
        sources = list(source_totals.get(key, {}).values())
        for source in sources:
            source.amount = round(source.amount, 2)
        sources.sort(
            key=lambda source: (not source.is_main_recipe, source.recipe_title.lower())
        )
        item.sources = sources
        item.amount = round(item.amount, 2)
        item.grams = round(item.grams, 2)
        item.calories = round(item.calories, 2)
        item.carbohydrates = round(item.carbohydrates, 2)
        item.fat = round(item.fat, 2)
        item.protein = round(item.protein, 2)
        result.append(item)

    result.sort(
        key=lambda item: (not item.has_overlap, item.title.lower(), item.unit.lower())
    )
    return result


def _build_recipe_public(
    session: SessionDep, recipe: Recipe, current_user: User | None = None
) -> RecipePublic:
    viewer_ids = None
    if _should_include_viewer_ids(current_user, recipe):
        viewer_ids = _get_viewer_ids(session, recipe.id)

    # Build full response payload including required aggregate fields.
    return RecipePublic.model_validate(
        {
            "id": recipe.id,
            "title": recipe.title,
            "instructions": recipe.instructions,
            "servings": recipe.servings,
            "image": recipe.image,
            "is_hidden": recipe.is_hidden,
            "owner": recipe.owner,
            "created_at": recipe.created_at,
            "ingredient_links": recipe.ingredient_links,
            "sub_recipe_links": recipe.sub_recipe_links,
            "total_ingredients": _calculate_total_ingredients(session, recipe),
            "viewer_ids": viewer_ids,
        }
    )


def _can_view_all_hidden(current_user: User | None) -> bool:
    if not current_user:
        return False
    if current_user.is_superuser:
        return True
    return "recipes:read_hidden" in get_user_effective_scopes(current_user)


def _is_allowed_viewer(
    session: SessionDep, recipe_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    viewer_link = session.exec(
        select(RecipeViewerLink).where(
            RecipeViewerLink.recipe_id == recipe_id,
            RecipeViewerLink.user_id == user_id,
        )
    ).first()
    return viewer_link is not None


def _can_view_recipe(
    session: SessionDep, recipe: Recipe, current_user: User | None
) -> bool:
    if not recipe.is_hidden:
        return True
    if not current_user:
        return False
    if recipe.owner_id == current_user.id:
        return True
    if _can_view_all_hidden(current_user):
        return True
    return _is_allowed_viewer(session, recipe.id, current_user.id)


def _should_include_viewer_ids(current_user: User | None, recipe: Recipe) -> bool:
    if not current_user:
        return False
    if current_user.is_superuser or recipe.owner_id == current_user.id:
        return True
    return "recipes:read_hidden" in get_user_effective_scopes(current_user)


def _can_edit_recipe(current_user: User, recipe: Recipe) -> bool:
    if current_user.is_superuser:
        return True
    if recipe.owner_id == current_user.id:
        return True
    return "recipes:update" in get_user_effective_scopes(current_user)


def _can_delete_recipe(current_user: User, recipe: Recipe) -> bool:
    if current_user.is_superuser:
        return True
    if recipe.owner_id == current_user.id:
        return True
    return "recipes:delete" in get_user_effective_scopes(current_user)


def _get_viewer_ids(session: SessionDep, recipe_id: uuid.UUID) -> list[uuid.UUID]:
    return session.exec(
        select(RecipeViewerLink.user_id).where(RecipeViewerLink.recipe_id == recipe_id)
    ).all()


def _validate_viewer_ids(
    session: SessionDep, viewer_ids: set[uuid.UUID]
) -> set[uuid.UUID]:
    if not viewer_ids:
        return set()
    existing_ids = set(
        session.exec(select(User.id).where(User.id.in_(viewer_ids))).all()
    )
    missing_ids = viewer_ids - existing_ids
    if missing_ids:
        missing_str = ", ".join(
            str(viewer_id) for viewer_id in sorted(missing_ids, key=str)
        )
        raise HTTPException(
            status_code=404, detail=f"Viewer(s) not found: {missing_str}"
        )
    return existing_ids


def _sync_recipe_viewers(
    session: SessionDep, recipe: Recipe, viewer_ids: set[uuid.UUID]
) -> None:
    viewer_ids.discard(recipe.owner_id)
    viewer_ids = _validate_viewer_ids(session, viewer_ids)

    existing_links = session.exec(
        select(RecipeViewerLink).where(RecipeViewerLink.recipe_id == recipe.id)
    ).all()
    existing_ids = {link.user_id for link in existing_links if link.user_id}

    to_remove = existing_ids - viewer_ids
    to_add = viewer_ids - existing_ids

    for link in existing_links:
        if link.user_id in to_remove:
            session.delete(link)

    for viewer_id in to_add:
        session.add(RecipeViewerLink(recipe_id=recipe.id, user_id=viewer_id))


@router.post("/upload-image")
def upload_recipe_image(
    file: UploadFile = File(...),
    current_user: User = Security(get_current_user, scopes=["recipes:create"]),
):
    """
    Upload an image for a recipe.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    settings = get_settings()
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )

    # Upload the file to Cloudinary
    # Use the environment to segregate uploads (e.g. "local/recipes", "production/recipes")
    folder_path = f"{settings.ENVIRONMENT}/recipes"
    upload_result = cloudinary.uploader.upload(file.file, folder=folder_path)

    return {"url": upload_result.get("secure_url")}


@router.get("/", response_model=list[RecipePublic])
def get_recipes(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    current_user: User | None = Security(get_current_user_optional),
):
    """
    Retrieve recipes.
    """

    statement = (
        select(Recipe).order_by(desc(Recipe.created_at)).offset(skip).limit(limit)
    )
    if not current_user:
        statement = statement.where(Recipe.is_hidden.is_(False))
    elif not _can_view_all_hidden(current_user):
        viewer_subquery = select(RecipeViewerLink.recipe_id).where(
            RecipeViewerLink.user_id == current_user.id
        )
        statement = statement.where(
            or_(
                Recipe.is_hidden.is_(False),
                Recipe.owner_id == current_user.id,
                Recipe.id.in_(viewer_subquery),
            )
        )
    recipes = session.exec(statement).all()

    return [_build_recipe_public(session, recipe, current_user) for recipe in recipes]


@router.get("/{recipe_id}", response_model=RecipePublic)
def get_recipe(
    session: SessionDep,
    recipe_id: str,
    current_user: User | None = Security(get_current_user_optional),
):
    """
    Retrieve a recipe.
    """
    # check valid uuid

    try:
        recipe = session.get(Recipe, recipe_id)
    except Exception:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if not _can_view_recipe(session, recipe, current_user):
        raise HTTPException(status_code=404, detail="Recipe not found")

    return _build_recipe_public(session, recipe, current_user)


@router.post("/", response_model=RecipePublic)
def create_recipe(
    session: SessionDep,
    recipe_in: RecipeCreate,
    current_user: User = Security(get_current_user, scopes=["recipes:create"]),
):
    """
    Create a new recipe.
    """
    _validate_unique_sub_recipe_ids(recipe_in)

    # create recipe without ingredients
    recipe = Recipe(
        title=recipe_in.title,
        instructions=recipe_in.instructions,
        owner_id=current_user.id,
        servings=recipe_in.servings,
        image=recipe_in.image,
        is_hidden=recipe_in.is_hidden,
    )

    session.add(recipe)
    session.flush()

    for ingredient_link in recipe_in.ingredients:
        ingredient = session.get(Ingredient, ingredient_link.ingredient_id)
        if not ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found")

        # create a new RecipeIngredientLink
        recipe_ingredient_link = RecipeIngredientLink(
            ingredient_id=ingredient_link.ingredient_id,
            recipe_id=recipe.id,  # Now recipe.id is valid
            amount=ingredient_link.amount,
            unit=ingredient_link.unit,
        )
        session.add(recipe_ingredient_link)

    _validate_sub_recipes_exist(session, recipe_in, recipe.id)
    _validate_no_sub_recipe_cycles(
        session,
        recipe.id,
        [sub_recipe_link.sub_recipe_id for sub_recipe_link in recipe_in.sub_recipes],
    )

    for sub_recipe_link in recipe_in.sub_recipes:
        session.add(
            RecipeSubRecipeLink(
                parent_recipe_id=recipe.id,
                sub_recipe_id=sub_recipe_link.sub_recipe_id,
                scale_factor=sub_recipe_link.scale_factor,
            )
        )

    if recipe_in.viewer_ids is not None:
        viewer_ids = set(recipe_in.viewer_ids)
        viewer_ids.discard(current_user.id)
        viewer_ids = _validate_viewer_ids(session, viewer_ids)
        for viewer_id in viewer_ids:
            session.add(RecipeViewerLink(recipe_id=recipe.id, user_id=viewer_id))

    session.commit()
    session.refresh(recipe)

    return _build_recipe_public(session, recipe, current_user)


@router.patch("/{recipe_id}", response_model=RecipePublic)
def update_recipe(
    session: SessionDep,
    recipe_id: str,
    recipe_in: RecipeCreate,
    current_user: User = Security(get_current_user),
):
    """
    Update a recipe.
    """
    # print(f"recipe_in 1: {recipe_in}")

    db_recipe = session.get(Recipe, recipe_id)
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if not _can_edit_recipe(current_user, db_recipe):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    _validate_unique_sub_recipe_ids(recipe_in)
    _validate_sub_recipes_exist(session, recipe_in, db_recipe.id)
    _validate_no_sub_recipe_cycles(
        session,
        db_recipe.id,
        [sub_recipe_link.sub_recipe_id for sub_recipe_link in recipe_in.sub_recipes],
    )

    # Get the new ingredient IDs from the request
    new_ingredient_ids = {link.ingredient_id for link in recipe_in.ingredients}

    # Get existing ingredient links from database
    existing_links = session.exec(
        select(RecipeIngredientLink).where(
            RecipeIngredientLink.recipe_id == db_recipe.id
        )
    ).all()

    # Delete ingredient links that are not in the new list
    for existing_link in existing_links:
        if existing_link.ingredient_id not in new_ingredient_ids:
            session.delete(existing_link)

    # update the ingredient links
    for ingredient_link in recipe_in.ingredients:
        existing_link = session.exec(
            select(RecipeIngredientLink).where(
                RecipeIngredientLink.recipe_id == db_recipe.id,
                RecipeIngredientLink.ingredient_id == ingredient_link.ingredient_id,
            )
        ).one_or_none()

        if existing_link:
            # Update existing link
            existing_link.amount = ingredient_link.amount
            existing_link.unit = ingredient_link.unit
        else:
            # Create new link
            new_link = RecipeIngredientLink(
                recipe_id=db_recipe.id,
                ingredient_id=ingredient_link.ingredient_id,
                amount=ingredient_link.amount,
                unit=ingredient_link.unit,
            )
            session.add(new_link)

    new_sub_recipe_ids = {link.sub_recipe_id for link in recipe_in.sub_recipes}
    existing_sub_recipe_links = session.exec(
        select(RecipeSubRecipeLink).where(
            RecipeSubRecipeLink.parent_recipe_id == db_recipe.id
        )
    ).all()

    for existing_sub_link in existing_sub_recipe_links:
        if existing_sub_link.sub_recipe_id not in new_sub_recipe_ids:
            session.delete(existing_sub_link)

    for sub_recipe_link in recipe_in.sub_recipes:
        existing_sub_link = session.exec(
            select(RecipeSubRecipeLink).where(
                RecipeSubRecipeLink.parent_recipe_id == db_recipe.id,
                RecipeSubRecipeLink.sub_recipe_id == sub_recipe_link.sub_recipe_id,
            )
        ).one_or_none()

        if existing_sub_link:
            existing_sub_link.scale_factor = sub_recipe_link.scale_factor
        else:
            session.add(
                RecipeSubRecipeLink(
                    parent_recipe_id=db_recipe.id,
                    sub_recipe_id=sub_recipe_link.sub_recipe_id,
                    scale_factor=sub_recipe_link.scale_factor,
                )
            )

    recipe_in_data = recipe_in.model_dump(
        exclude_unset=True, exclude={"ingredients", "sub_recipes", "viewer_ids"}
    )
    db_recipe.sqlmodel_update(recipe_in_data)
    session.add(db_recipe)

    if recipe_in.viewer_ids is not None:
        _sync_recipe_viewers(session, db_recipe, set(recipe_in.viewer_ids))

    session.commit()
    session.refresh(db_recipe)

    return _build_recipe_public(session, db_recipe, current_user)


@router.delete("/{recipe_id}", response_model=Recipe)
def delete_recipe(
    session: SessionDep,
    recipe_id: str,
    current_user: User = Security(get_current_user),
):
    """
    Delete a recipe.
    """

    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if not _can_delete_recipe(current_user, recipe):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Delete associated ingredient links first (optional since we have cascade_delete=True)
    # for link in recipe.ingredient_links:
    #     session.delete(link)

    session.delete(recipe)
    session.commit()
    return recipe
