import logging
import os
from sqlmodel import Session, select

from app.db import (
    engine,
    init_db,
)
from app import db_crud
from app.models import (
    GameSession,
    User,
    GameTeam,
    GamePlayer,
    Drink,
    GamePlayerDrinkLink,
    GamePlayerDrinkLinkCreate,
)
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init():
    with Session(engine) as session:
        logger.info("Creating superuser if none exists")
        init_db(session)
        # create_drinks(session)
        # create_game_session(session, session_name="Game Session 4")
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
            name=f"Team {i+1}",
            game_session_id=game_session.id,
        )
        session.add(team)
        session.commit()
        session.refresh(team)

        for j in range(5):
            player = GamePlayer(
                name=f"Player {j+1} (Team {i+1})",
                game_session_id=game_session.id,
                team_id=team.id,
            )
            session.add(player)
        session.commit()

        logger.info("Game session created")

def add_drinks_to_players(session: Session):
    """
        Add drinks to players
    """
    logger.info("Adding drinks to players")
    game_session = session.exec(
        select(GameSession).where(GameSession.title == "Game Session 4")
    ).first()
    assert game_session

    players = session.exec(
        select(GamePlayer).where(GamePlayer.game_session_id == game_session.id)
    ).all()
    assert players

    # get all drinks
    drinks = session.exec(
        select(Drink)
    ).all()
    assert drinks

    # add drinks to players - for now just add the first 2 drinks to the first player

    player_1 = players[1]

    player_1_drink_link = GamePlayerDrinkLink(
        game_player=player_1,
        drink=drinks[0],
    )
    player_1_drink_link_2 = GamePlayerDrinkLink(
        game_player=player_1,
        drink=drinks[1],
    )
    session.add(player_1_drink_link)
    session.add(player_1_drink_link_2)
    session.commit()
    session.refresh(player_1_drink_link)
    session.refresh(player_1_drink_link_2)
    logger.info(f"Added drink {drinks[0].name} to player {player_1.name}")
    logger.info("Drinks added to players")







def main():
    logger.info("Creating initial game data")
    init()
    logger.info("Initial game data created")

if __name__ == "__main__":
    main()

