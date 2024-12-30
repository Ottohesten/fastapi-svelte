from sqlmodel import Session, create_engine, select

import app.db_crud as db_crud
from app.config import settings
from app.models import User, UserCreate
from app.models import Hero


# engine = create_engine("sqlite:///database.db")

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

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
    

    # create heroes initial data
    hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
    hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
    hero_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)

    session.add(hero_1)
    session.add(hero_2)
    session.add(hero_3)
    session.commit()
