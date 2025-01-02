from fastapi import APIRouter
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlmodel import select
from app.deps import SessionDep, CurrentUser
from app.models import Recipe, RecipeCreate



router = APIRouter(prefix="/recipes", tags=["recipes"])



@router.get("/", response_model=list[Recipe])
def read_recipes(session: SessionDep, skip: int = 0, limit: int = 100):
    """
    Retrieve recipes.
    """

    statement = select(Recipe).offset(skip).limit(limit)
    recipes = session.exec(statement).all()

    return recipes


@router.get("/{recipe_id}", response_model=Recipe)
def read_recipe(session: SessionDep, recipe_id: str):
    """
    Retrieve a recipe.
    """

    statement = select(Recipe).where(Recipe.id == recipe_id)
    recipe = session.exec(statement).first()

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    print(recipe)

    return recipe


@router.post("/", response_model=Recipe)
def create_recipe(session: SessionDep, current_user: CurrentUser, recipe_in: RecipeCreate):
    """
    Create a new recipe.
    """
    recipe = Recipe.model_validate(recipe_in, update={"owner_id": current_user.id})
    session.add(recipe)
    session.commit()
    session.refresh(recipe)


    return recipe