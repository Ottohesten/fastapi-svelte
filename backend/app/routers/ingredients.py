from fastapi import APIRouter
from fastapi import FastAPI, Depends, HTTPException, status, Query, Security
from sqlmodel import select
from app.deps import SessionDep, CurrentUser, get_current_user
# from app.models import Recipe, RecipeCreate, RecipePublic
from app.models import Ingredient, IngredientBase, IngredientCreate, IngredientPublic, User


router = APIRouter(prefix="/ingredients", tags=["ingredients"])

@router.get("/", response_model=list[IngredientPublic])
def read_ingredients(session: SessionDep, skip: int = 0, limit: int = 100):
    """
    Retrieve ingredients.
    """

    statement = select(Ingredient).offset(skip).limit(limit)
    ingredients = session.exec(statement).all()

    return ingredients


@router.get("/{ingredient_id}", response_model=IngredientPublic)
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


@router.post("/", response_model=IngredientPublic)
def create_ingredient(
    session: SessionDep, 
    ingredient_in: IngredientCreate,
    current_user: User = Security(get_current_user, scopes=["ingredients:create"])
):
    """
    Create a new ingredient.
    """
    ingredient = Ingredient.model_validate(ingredient_in)
    session.add(ingredient)
    session.commit()
    session.refresh(ingredient)


    return ingredient


@router.delete("/{ingredient_id}", response_model=IngredientPublic)
def delete_ingredient(
    session: SessionDep, 
    ingredient_id: str,
    current_user: User = Security(get_current_user, scopes=["ingredients:delete"])
):
    """
    Delete a ingredient.
    """
    ingredient = session.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    session.delete(ingredient)
    session.commit()

    return ingredient


@router.patch("/{ingredient_id}", response_model=IngredientPublic)
def update_ingredient(
    session: SessionDep, 
    ingredient_id: str, 
    ingredient_in: IngredientCreate,
    current_user: User = Security(get_current_user, scopes=["ingredients:update"])
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
    session.commit()
    session.refresh(ingredient)
    return ingredient