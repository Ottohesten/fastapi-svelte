from fastapi import APIRouter
from fastapi import HTTPException, Security, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from app.deps import SessionDep, get_current_user

# from app.models import Recipe, RecipeCreate, RecipePublic
from app.models import (
    Ingredient,
    IngredientCreate,
    IngredientPublic,
    OpenFoodFactsProductPublic,
    User,
    RecipeIngredientLink,
)
from app.openfoodfacts import (
    OpenFoodFactsUnavailableError,
    ProductNotFoundError,
    lookup_product,
)


router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("/", response_model=list[IngredientPublic])
def get_ingredients(session: SessionDep, skip: int = 0, limit: int = 100):
    """
    Retrieve ingredients.
    """

    statement = select(Ingredient).offset(skip).limit(limit)
    ingredients = session.exec(statement).all()

    return ingredients


@router.get("/barcode/{barcode}", response_model=OpenFoodFactsProductPublic)
def get_ingredient_by_barcode(
    session: SessionDep,
    barcode: str,
    current_user: User = Security(get_current_user, scopes=["ingredients:create"]),
):
    """Look up a packaged food in Open Food Facts by barcode."""
    try:
        normalized_barcode = IngredientCreate.normalize_barcode(barcode)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if normalized_barcode is None:
        raise HTTPException(status_code=422, detail="Barcode is required")

    try:
        product = lookup_product(normalized_barcode)
    except ProductNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail="Product not found in Open Food Facts"
        ) from exc
    except OpenFoodFactsUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Open Food Facts is temporarily unavailable. Please try again.",
        ) from exc

    existing = session.exec(
        select(Ingredient).where(Ingredient.barcode == product.barcode)
    ).first()
    if existing:
        product.existing_ingredient_id = existing.id
    return product


@router.get("/{ingredient_id}", response_model=IngredientPublic)
def get_ingredient(session: SessionDep, ingredient_id: str):
    """
    Retrieve a ingredient.
    """
    # check valid uuid

    try:
        ingredient = session.get(Ingredient, ingredient_id)
    except Exception:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    return ingredient


@router.post("/", response_model=IngredientPublic)
def create_ingredient(
    session: SessionDep,
    ingredient_in: IngredientCreate,
    current_user: User = Security(get_current_user, scopes=["ingredients:create"]),
):
    """
    Create a new ingredient.
    """
    ingredient = Ingredient.model_validate(ingredient_in)
    session.add(ingredient)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An ingredient with this barcode already exists",
        ) from exc
    session.refresh(ingredient)

    return ingredient


@router.delete("/{ingredient_id}", response_model=IngredientPublic)
def delete_ingredient(
    session: SessionDep,
    ingredient_id: str,
    current_user: User = Security(get_current_user, scopes=["ingredients:delete"]),
):
    """
    Delete a ingredient.
    """
    ingredient = session.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    # Check if the ingredient is used in any recipes
    recipe_links = session.exec(
        select(RecipeIngredientLink).where(
            RecipeIngredientLink.ingredient_id == ingredient_id
        )
    ).all()

    if recipe_links:
        # Delete all recipe ingredient links first
        for link in recipe_links:
            session.delete(link)
        session.flush()  # Ensure links are deleted before deleting the ingredient

    session.delete(ingredient)
    session.commit()

    return ingredient


@router.patch("/{ingredient_id}", response_model=IngredientPublic)
def update_ingredient(
    session: SessionDep,
    ingredient_id: str,
    ingredient_in: IngredientCreate,
    current_user: User = Security(get_current_user, scopes=["ingredients:update"]),
):
    """
    Update an ingredient.
    """
    ingredient = session.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    ingredient_data = ingredient_in.model_dump(exclude_unset=True)
    ingredient.sqlmodel_update(ingredient_data)
    session.add(ingredient)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An ingredient with this barcode already exists",
        ) from exc
    session.refresh(ingredient)
    return ingredient
