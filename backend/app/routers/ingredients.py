from fastapi import APIRouter
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlmodel import select
from app.deps import SessionDep, CurrentUser, get_current_active_superuser
# from app.models import Recipe, RecipeCreate, RecipePublic
from app.models import Ingredient, IngredientBase, IngredientCreate


router = APIRouter(prefix="/ingredients", tags=["ingredients"])

@router.get("/", response_model=list[Ingredient])
def read_ingredients(session: SessionDep, skip: int = 0, limit: int = 100):
    """
    Retrieve ingredients.
    """

    statement = select(Ingredient).offset(skip).limit(limit)
    ingredients = session.exec(statement).all()

    return ingredients


@router.get("/{ingredient_id}", response_model=Ingredient)
def read_ingredient(session: SessionDep, ingredient_id: str):
    """
    Retrieve a ingredient.
    """
    # check valid uuid

    try:
        ingredient = session.get(Ingredient, ingredient_id)
    except Exception as e:
    # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    return ingredient


@router.post("/", response_model=Ingredient)
def create_ingredient(session: SessionDep, current_user: CurrentUser, ingredient_in: IngredientCreate):
    """
    Create a new ingredient.
    """
    ingredient = Ingredient.model_validate(ingredient_in)
    session.add(ingredient)
    session.commit()
    session.refresh(ingredient)


    return ingredient
