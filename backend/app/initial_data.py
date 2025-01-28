import logging

from sqlmodel import Session

from app.db import engine, init_db, create_ingredients_and_recipes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    with Session(engine) as session:
        # init_db(session)
        create_ingredients_and_recipes(session)



def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()