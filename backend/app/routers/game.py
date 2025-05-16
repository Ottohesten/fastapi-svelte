from fastapi import APIRouter
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlmodel import select
from app.deps import SessionDep, CurrentUser, get_current_active_superuser

from app.models import (
    GameSession, 
    GameSessionCreate, 
    GameSessionPublic,
    GameSessionUpdate,
    GamePlayer,
    GamePlayerCreate,
    GamePlayerPublic,
    GameTeam,
    GameTeamCreate,
    GameTeamPublic
)


router = APIRouter(prefix="/game", tags=["game"])

@router.get("/", response_model=list[GameSessionPublic])
def read_game_sessions(session: SessionDep, skip: int = 0, limit: int = 100):
    """
    Retrieve game sessions.
    """
    statement = select(GameSession).offset(skip).limit(limit)
    game_sessions = session.exec(statement).all()

    return game_sessions


@router.get("/{game_session_id}", response_model=GameSessionPublic)
def read_game_session(session: SessionDep, game_session_id: str):
    """
    Retrieve a game session.
    """
    # check valid uuid

    try:
        game_session = session.get(GameSession, game_session_id)
    except Exception as e:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")

    return game_session


@router.post("/", response_model=GameSessionPublic)
def create_game_session(session: SessionDep, current_user: CurrentUser, game_session_in: GameSessionCreate):
    """
    Create a new game session.
    """
    game_teams = [GameTeam(**team.model_dump()) for team in game_session_in.teams] if game_session_in.teams else []
    # print(game_teams)

    game_session = GameSession(
        **game_session_in.model_dump(exclude={"teams"}),  # Unpack the dictionary into the model
        owner_id=current_user.id,
        teams=game_teams,
    )

    # game_session = GameSession.model_validate(game_session_in, update={"owner_id": current_user.id})
    session.add(game_session)
    session.commit()
    session.refresh(game_session)

    # update the 

    return game_session

# delete game session
@router.delete("/{game_session_id}", response_model=GameSessionPublic)
def delete_game_session(session: SessionDep, game_session_id: str, current_user: CurrentUser):
    """
    Delete a game session.
    """
    # check valid uuid
    try:
        game_session = session.get(GameSession, game_session_id)
    except Exception as e:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")

    if game_session.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to delete this game session")

    session.delete(game_session)
    session.commit()

    return game_session



# make player and add to game session
@router.post("/{game_session_id}/player", response_model=GamePlayerPublic)
def create_game_player(session: SessionDep, game_session_id: str, game_player_in: GamePlayerCreate, current_user: CurrentUser):
    """
    Create a new game player.
    """
    # check valid uuid
    try:
        game_session = session.get(GameSession, game_session_id)
    except Exception as e:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")

    # game_player = GamePlayer(
    #     name=game_player_in.name,
    #     game_session_id=game_session.id,
    # )

    game_player = GamePlayer.model_validate(game_player_in, update={"game_session_id": game_session.id} )
    session.add(game_player)
    session.commit()
    session.refresh(game_player)

    return game_player



# make team and add to game session
@router.post("/{game_session_id}/team", response_model=GameTeamPublic)
def create_game_team(session: SessionDep, game_session_id: str, game_team_in: GameTeamCreate, current_user: CurrentUser):
    """
    Create a new game team.
    """
    # check valid uuid
    try:
        game_session = session.get(GameSession, game_session_id)
    except Exception as e:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")

    # game_player = GamePlayer(
    #     name=game_player_in.name,
    #     game_session_id=game_session.id,
    # )

    game_team = GameTeam.model_validate(game_team_in, update={"game_session_id": game_session.id} )
    session.add(game_team)
    session.commit()
    session.refresh(game_team)

    return game_team

# delete game player
@router.delete("/{game_session_id}/player/{game_player_id}", response_model=GamePlayerPublic)
def delete_game_player(session: SessionDep, game_session_id: str, game_player_id: str, current_user: CurrentUser):
    """
    Delete a game player.
    """
    # check valid uuid
    try:
        game_session = session.get(GameSession, game_session_id)
    except Exception as e:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")

    # check valid uuid
    try:
        game_player = session.get(GamePlayer, game_player_id)
    except Exception as e:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_player:
        raise HTTPException(status_code=404, detail="Game player not found")

    if game_player.game_session_id != game_session.id:
        raise HTTPException(status_code=404, detail="Game player not found in this game session")

    session.delete(game_player)
    session.commit()

    return game_player

# delete game team
@router.delete("/{game_session_id}/team/{game_team_id}", response_model=GameTeamPublic)
def delete_game_team(session: SessionDep, game_session_id: str, game_team_id: str, current_user: CurrentUser):
    """
    Delete a game team.
    """
    # check valid uuid
    try:
        game_session = session.get(GameSession, game_session_id)
    except Exception as e:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")

    # check valid uuid
    try:
        game_team = session.get(GameTeam, game_team_id)
    except Exception as e:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_team:
        raise HTTPException(status_code=404, detail="Game team not found")

    if game_team.game_session_id != game_session.id:
        raise HTTPException(status_code=404, detail="Game team not found in this game session")

    session.delete(game_team)
    session.commit()

    return game_team
