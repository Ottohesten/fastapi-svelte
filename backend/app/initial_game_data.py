import logging
from sqlmodel import Session, select

from app.db import (
    engine,
    init_db,
)
from app.models import (
    GameSession,
    User,
    GameTeam,
    GamePlayer,
    Drink,
    GamePlayerDrinkLink,
)
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init():
    with Session(engine) as session:
        logger.info("Creating superuser if none exists")
        init_db(session)
        # create_drinks(session)
        create_game_session(session, session_name="Game Session 6")
        add_drinks_to_players(session)


def create_drinks(session: Session):
    """
    Create drinks that can be added to players later
    (the drinks are cocktails)
    """
    logger.info("Creating drinks")

    drinks = [
        Drink(name="Mojito"),
        Drink(name="Margarita"),
        Drink(name="Pina Colada"),
        Drink(name="Daiquiri"),
        Drink(name="Mai Tai"),
        Drink(name="Old Fashioned"),
        Drink(name="Whiskey Sour"),
        Drink(name="Cosmopolitan"),
        Drink(name="Martini"),
        Drink(name="Bloody Mary"),
        Drink(name="Gin and Tonic"),
    ]

    # save to database
    for drink in drinks:
        session.add(drink)
    session.commit()
    session.refresh(drink)

    logger.info("Drinks created")


def create_game_session(session: Session, session_name: str = "Game Session 1"):
    logger.info("Creating game session")

    superuser = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    assert superuser

    game_session = GameSession(
        title=f"{session_name}",
        owner_id=superuser.id,
    )
    session.add(game_session)
    session.commit()
    session.refresh(game_session)

    for i in range(3):
        team = GameTeam(
            name=f"Team {i + 1}",
            game_session_id=game_session.id,
        )
        session.add(team)
        session.commit()
        session.refresh(team)

        for j in range(5):
            player = GamePlayer(
                name=f"Player {j + 1} (Team {i + 1})",
                game_session_id=game_session.id,
                team_id=team.id,
            )
            session.add(player)
        session.commit()

        logger.info("Game session created")


def add_drinks_to_players(session: Session):
    """
    Add drinks to players with varied amounts for better chart visualization
    """
    import random

    logger.info("Adding drinks to players")
    game_session = session.exec(
        select(GameSession).where(GameSession.title == "Game Session 6")
    ).first()
    assert game_session

    players = session.exec(
        select(GamePlayer).where(GamePlayer.game_session_id == game_session.id)
    ).all()
    assert players

    # get all drinks
    drinks = session.exec(select(Drink)).all()
    assert drinks

    # Add varied drinks to first 10 players for better chart visualization
    for i in range(min(10, len(players))):
        player = players[i]

        # Each player gets 1-5 different drinks with amounts 1-3
        num_drinks = random.randint(1, 5)
        selected_drinks = random.sample(drinks, min(num_drinks, len(drinks)))

        for drink in selected_drinks:
            amount = random.randint(1, 3)
            drink_link = GamePlayerDrinkLink(
                game_player=player, drink=drink, amount=amount
            )
            session.add(drink_link)
            logger.info(f"Added {amount} x {drink.name} to player {player.name}")

    session.commit()
    logger.info("Enhanced drinks added to players for chart visualization")


def main():
    logger.info("Creating initial game data")
    init()
    logger.info("Initial game data created")


if __name__ == "__main__":
    main()
