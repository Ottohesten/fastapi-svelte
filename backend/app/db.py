from sqlmodel import Session, create_engine, select

import app.db_crud as db_crud
from app.config import settings
from app.models import User, UserCreate
from app.models import Hero
from app.models import IngredientCreate, RecipeCreate, Ingredient, Recipe


# if we actually want to use SQLite, we can use the following line
# engine = create_engine("sqlite:///database.db")


# Make sure to actually create the database
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
# print(engine)

# print("***************************************")
# print("database uri")
# print(settings.SQLALCHEMY_DATABASE_URI)


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = db_crud.create_user(session=session, user_create=user_in)

        print("Superuser created")
    else:
        print("Superuser already exists")

    # check if there already are heroes in the database
    

# def create_ingredients_and_recipes(session: Session):
#     ingredient_1 = Ingredient(title="Tomato")
#     ingredient_2 = Ingredient(title="Onion")
#     session.add(ingredient_1)
#     session.add(ingredient_2) 
#     session.commit()
#     session.refresh(ingredient_1)
#     session.refresh(ingredient_2)

#     print("Ingredient created")

#     # recipe_1 = Recipe(title="Tomato Soup", owner_id=user.id)
#     recipe_1 = Recipe(title="Tomato Soup", owner_id="9d4b9156-f5a7-4181-ac0f-4628de0cd551", ingredients=[ingredient_1, ingredient_2])
#     recipe_2 = Recipe(title="Onion Soup", owner_id="9d4b9156-f5a7-4181-ac0f-4628de0cd551", ingredients=[ingredient_2])

#     session.add(recipe_1)
#     session.add(recipe_2)
#     session.commit()
#     session.refresh(recipe_1)
#     session.refresh(recipe_2)
    
#     print("Recipe created")

# def create_heroes(session: Session):
#     print("checking if heroes exist")
#     heroes = session.exec(select(Hero).where(Hero.name == "Deadpond")).first()
#     print(f"Heroes: {heroes}")
#     if not heroes:
#         print("creating heroes")
#         # create heroes initial data
#         hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
#         hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
#         hero_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)
    
#         session.add(hero_1)
#         session.add(hero_2)
#         session.add(hero_3)
#         session.commit()
