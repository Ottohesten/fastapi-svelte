from fastapi import APIRouter
from fastapi import FastAPI, Depends, HTTPException, status, Query, Security
from sqlmodel import select
from app.deps import SessionDep, CurrentUser, get_current_user
from app.models import Recipe, RecipeCreate, RecipeIngredientLink, RecipePublic, Ingredient, User



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


@router.post("/", response_model=RecipePublic)
def create_recipe(
    session: SessionDep, 
    recipe_in: RecipeCreate,
    current_user: User = Security(get_current_user, scopes=["recipes:create"])
):
    """
    Create a new recipe.
    """

    # create recipe without ingredients
    recipe = Recipe(
        title=recipe_in.title,
        instructions=recipe_in.instructions,
        owner_id=current_user.id
    )

    # session.add(recipe)
    # session.commit()
    # session.refresh(recipe)





    # get ingredients
    # for ingredient in recipe_in.ingredients:
    #     ingredient = session.get(Ingredient, ingredient.id)
    #     if not ingredient:
    #         raise HTTPException(status_code=404, detail="Ingredient not found")
    #     recipe.ingredients.append(ingredient)
    ingredient_links = recipe_in.ingredients

    for ingredient_link in ingredient_links:
        ingredient = session.get(Ingredient, ingredient_link.ingredient_id)
        if not ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        
        # check if there is already a link for this ingredient in the recipe
        # statement = select(RecipeIngredientLink).where(
        #     RecipeIngredientLink.ingredient_id == ingredient_link.ingredient_id,
        #     RecipeIngredientLink.recipe_id == recipe.id
        # )
        # existing_link = session.exec(statement).first()
        # if existing_link:
        #     raise HTTPException(
        #         status_code=400, 
        #         detail=f"Ingredient {ingredient.title} is already linked to this recipe"
        #     )
        
        # create a new RecipeIngredientLink
        recipe_ingredient_link = RecipeIngredientLink(
            ingredient_id=ingredient_link.ingredient_id,
            recipe_id=recipe.id,
            amount=ingredient_link.amount,
            unit=ingredient_link.unit
        )
        # print(f"recipe_ingredient_link: {recipe_ingredient_link}")
        session.add(recipe_ingredient_link)
    
    session.add(recipe)
    session.commit()
    session.refresh(recipe)


    return recipe


# @router.patch("/{recipe_id}", response_model=RecipePublic)
# def update_recipe(
#     session: SessionDep, 
#     recipe_id: str, 
#     recipe_in: RecipeCreate,
#     current_user: User = Security(get_current_user, scopes=["recipes:update"])
# ):
#     """
#     Update a recipe.
#     """
#     print(f"recipe_in 1: {recipe_in}")

#     db_recipe = session.get(Recipe, recipe_id)
#     if not db_recipe:
#         raise HTTPException(status_code=404, detail="Recipe not found")
    

#     ingredients = []
#     for ingredient in recipe_in.ingredients:
#         ingredient = session.get(Ingredient, ingredient.id)
#         if not ingredient:
#             raise HTTPException(status_code=404, detail="Ingredient not found")
#         ingredients.append(ingredient)
#     # recipe_in.ingredients = ingredients
#     # print(f"recipe_in 2: {recipe_in}")

    
#     db_recipe.ingredients = ingredients # required to update the relationship
    
#     recipe_data = recipe_in.model_dump(exclude_unset=True)
#     # recipe_data = recipe_in.model_dump()
#     # print(recipe_data)
#     db_recipe.sqlmodel_update(recipe_data)
#     # db_recipe.sqlmodel_update(recipe_data, update={"ingredients": ingredients})
#     # print(f"db_recipe: {db_recipe}")
#     session.add(db_recipe)
#     session.commit()
#     session.refresh(db_recipe)
#     return db_recipe


@router.delete("/{recipe_id}", response_model=Recipe)
def delete_recipe(
    session: SessionDep, 
    recipe_id: str,
    current_user: User = Security(get_current_user, scopes=["recipes:delete"])
):
    """
    Delete a recipe.
    """

    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Delete associated ingredient links first (optional since we have cascade_delete=True)
    # for link in recipe.ingredient_links:
    #     session.delete(link)
    
    session.delete(recipe)
    session.commit()
    return recipe
