from fastapi import APIRouter
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlmodel import select
from app.deps import SessionDep, CurrentUser, get_current_active_superuser
from app.models import Recipe, RecipeCreate, RecipePublic



router = APIRouter(prefix="/recipes", tags=["recipes"])



@router.get("/", response_model=list[RecipePublic])
def read_recipes(session: SessionDep, skip: int = 0, limit: int = 100):
    """
    Retrieve recipes.
    """

    statement = select(Recipe).offset(skip).limit(limit)
    recipes = session.exec(statement).all()

    # for recipe in recipes:
    #     print(recipe.owner)

    return recipes


@router.get("/{recipe_id}", response_model=RecipePublic)
def read_recipe(session: SessionDep, recipe_id: str):
    """
    Retrieve a recipe.
    """
    # check valid uuid

    try:
        recipe = session.get(Recipe, recipe_id)
    except Exception as e:
    # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

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


@router.patch("/{recipe_id}", dependencies=[Depends(get_current_active_superuser)], response_model=Recipe)
def update_recipe(session: SessionDep, recipe_id: str, recipe_in: RecipeCreate):
    """
    Update a recipe.
    """

    db_recipe = session.get(Recipe, recipe_id)
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    recipe_data = recipe_in.model_dump(exclude_unset=True)
    db_recipe.sqlmodel_update(recipe_data)
    session.add(db_recipe)
    session.commit()
    session.refresh(db_recipe)
    return db_recipe


@router.delete("/{recipe_id}", dependencies=[Depends(get_current_active_superuser)], response_model=Recipe)
def delete_recipe(session: SessionDep, recipe_id: str):
    """
    Delete a recipe.
    """

    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    session.delete(recipe)
    session.commit()
    return recipe
