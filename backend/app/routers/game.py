from fastapi import APIRouter
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlmodel import select
from app.deps import SessionDep, CurrentUser, get_current_active_superuser

from app.models import GameSession, GameSessionCreate, GameSessionPublic


router = APIRouter(prefix="/game", tags=["game"])

@router.get("/", response_model=list[GameSession])
def read_game_sessions(session: SessionDep, skip: int = 0, limit: int = 100):
    """
    Retrieve game sessions.
    """
    statement = select(GameSession).offset(skip).limit(limit)
    game_sessions = session.exec(statement).all()

    return game_sessions


@router.get("/{game_session_id}", response_model=GameSession)
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
    game_session = GameSession.model_validate(game_session_in, update={"owner_id": current_user.id} )
    session.add(game_session)
    session.commit()
    session.refresh(game_session)

    return game_session
