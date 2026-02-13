from fastapi import APIRouter, UploadFile, File
from fastapi import HTTPException, Security
from sqlmodel import select
import cloudinary
import cloudinary.uploader
from app.config import get_settings
from app.deps import SessionDep, get_current_user
from app.models import (
    Recipe,
    RecipeCreate,
    RecipeIngredientLink,
    RecipePublic,
    Ingredient,
    User,
)


router = APIRouter(prefix="/recipes", tags=["recipes"])


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
def get_recipes(session: SessionDep, skip: int = 0, limit: int = 100):
    """
    Retrieve recipes.
    """

    statement = select(Recipe).offset(skip).limit(limit)
    recipes = session.exec(statement).all()

    # for recipe in recipes:
    #     print(recipe.owner)

    return recipes


@router.get("/{recipe_id}", response_model=RecipePublic)
def get_recipe(session: SessionDep, recipe_id: str):
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

    return recipe


@router.post("/", response_model=RecipePublic)
def create_recipe(
    session: SessionDep,
    recipe_in: RecipeCreate,
    current_user: User = Security(get_current_user, scopes=["recipes:create"]),
):
    """
    Create a new recipe.
    """

    # create recipe without ingredients
    recipe = Recipe(
        title=recipe_in.title,
        instructions=recipe_in.instructions,
        owner_id=current_user.id,
        servings=recipe_in.servings,
        image=recipe_in.image,
    )

    # Save the recipe first to get a valid ID
    session.add(recipe)
    session.commit()
    session.refresh(recipe)

    # Now create ingredient links
    ingredient_links = recipe_in.ingredients

    for ingredient_link in ingredient_links:
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

    # Commit the ingredient links
    session.commit()
    session.refresh(recipe)

    return recipe


@router.patch("/{recipe_id}", response_model=RecipePublic)
def update_recipe(
    session: SessionDep,
    recipe_id: str,
    recipe_in: RecipeCreate,
    current_user: User = Security(get_current_user, scopes=["recipes:update"]),
):
    """
    Update a recipe.
    """
    # print(f"recipe_in 1: {recipe_in}")

    db_recipe = session.get(Recipe, recipe_id)
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

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

    recipe_in_data = recipe_in.model_dump(exclude_unset=True, exclude={"ingredients"})
    db_recipe.sqlmodel_update(recipe_in_data)
    session.add(db_recipe)
    session.commit()
    session.refresh(db_recipe)

    return db_recipe


@router.delete("/{recipe_id}", response_model=Recipe)
def delete_recipe(
    session: SessionDep,
    recipe_id: str,
    current_user: User = Security(get_current_user, scopes=["recipes:delete"]),
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
