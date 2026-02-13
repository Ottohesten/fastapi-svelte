from fastapi import APIRouter, BackgroundTasks
from fastapi import HTTPException, Security
from fastapi.responses import StreamingResponse
from sqlmodel import select, asc
from app.deps import SessionDep, get_current_user
from typing import Annotated
import asyncio
import json
from datetime import datetime, timezone

from app.models import (
    GameSession,
    GameSessionCreate,
    GameSessionPublic,
    GamePlayer,
    GamePlayerCreate,
    GamePlayerUpdate,
    GamePlayerPublic,
    GameTeam,
    GameTeamCreate,
    GameTeamPublic,
    Drink,
    DrinkPublic,
    DrinkCreate,
    GamePlayerDrinkLink,
    GamePlayerDrinkLinkCreate,
    User,
)
from app.permissions import get_user_effective_scopes

# Store active SSE connections for each game session
from collections import defaultdict

game_session_subscribers = defaultdict(list)


# Helper function to broadcast updates to all subscribers of a game session
async def broadcast_game_update(game_session_id: str, event_type: str):
    """Broadcast an update event to all subscribers of a specific game session"""
    if game_session_id in game_session_subscribers:
        # Create the message to send
        message = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "game_session_id": game_session_id,
        }

        # Send to all subscribers (queues)
        for queue in game_session_subscribers[game_session_id]:
            try:
                await queue.put(message)
            except Exception as e:
                print(f"Error broadcasting to subscriber: {e}")


router = APIRouter(prefix="/game", tags=["game"])


@router.get("/", response_model=list[GameSessionPublic])
def get_game_sessions(session: SessionDep, skip: int = 0, limit: int = 100):
    """
    Retrieve game sessions.
    """
    statement = (
        select(GameSession)
        .order_by(asc(GameSession.created_at))
        .offset(skip)
        .limit(limit)
    )
    game_sessions = session.exec(statement).all()

    return game_sessions


# get all drinks
@router.get("/drinks", response_model=list[DrinkPublic])
def get_drinks(session: SessionDep, skip: int = 0, limit: int = 100):
    """
    Retrieve drinks.
    """
    # print("Getting drinks")
    statement = select(Drink).offset(skip).limit(limit)
    drinks = session.exec(statement).all()
    return drinks


@router.post("/drinks", response_model=DrinkPublic)
def create_drink(
    session: SessionDep,
    drink_in: DrinkCreate,
    current_user: User = Security(get_current_user, scopes=["drinks:create"]),
):
    """
    Create a new drink.
    """
    drink = Drink.model_validate(drink_in)
    session.add(drink)
    session.commit()
    session.refresh(drink)

    return drink


@router.patch("/drinks/{drink_id}", response_model=DrinkPublic)
def update_drink(
    session: SessionDep,
    drink_id: str,
    drink_in: DrinkCreate,
    current_user: User = Security(get_current_user, scopes=["drinks:update"]),
):
    """
    Update a drink.
    """
    try:
        drink = session.get(Drink, drink_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found")

    drink_data = drink_in.model_dump(exclude_unset=True)
    drink.sqlmodel_update(drink_data)
    session.add(drink)
    session.commit()
    session.refresh(drink)

    return drink


@router.delete("/drinks/{drink_id}")
def delete_drink(
    session: SessionDep,
    drink_id: str,
    current_user: User = Security(get_current_user, scopes=["drinks:delete"]),
):
    """
    Delete a drink.
    """
    try:
        drink = session.get(Drink, drink_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found")

    session.delete(drink)
    session.commit()

    return {"success": True}


@router.get("/{game_session_id}", response_model=GameSessionPublic)
def get_game_session(session: SessionDep, game_session_id: str):
    """
    Retrieve a game session.
    """
    # check valid uuid

    try:
        game_session = session.get(GameSession, game_session_id)
    except Exception:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")

    return game_session


@router.post("/", response_model=GameSessionPublic)
def create_game_session(
    session: SessionDep,
    current_user: Annotated[User, Security(get_current_user, scopes=["games:create"])],
    game_session_in: GameSessionCreate,
):
    """
    Create a new game session.
    """
    game_teams = (
        [GameTeam(**team.model_dump()) for team in game_session_in.teams]
        if game_session_in.teams
        else []
    )
    # print(game_teams)

    game_session = GameSession(
        **game_session_in.model_dump(
            exclude={"teams"}
        ),  # Unpack the dictionary into the model
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
@router.delete("/{game_session_id}")
def delete_game_session(
    session: SessionDep,
    game_session_id: str,
    current_user: User = Security(get_current_user),
):
    """
    Delete a game session. Users can delete their own game sessions.
    """
    # check valid uuid
    try:
        game_session = session.get(GameSession, game_session_id)
    except Exception:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")

    # Allow delete if owner or user has games:delete scope.
    if game_session.owner_id != current_user.id:
        scopes = get_user_effective_scopes(current_user)
        if "games:delete" not in scopes:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this game session"
            )

    session.delete(game_session)
    session.commit()

    return {"success": True}


# make player and add to game session
@router.post("/{game_session_id}/player", response_model=GamePlayerPublic)
def create_game_player(
    session: SessionDep,
    game_session_id: str,
    game_player_in: GamePlayerCreate,
    current_user: User = Security(
        get_current_user, scopes=["games:update", "players:create"]
    ),
):
    """
    Create a new game player.
    """
    # check valid uuid
    try:
        game_session = session.get(GameSession, game_session_id)
    except Exception:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")

    # game_player = GamePlayer(
    #     name=game_player_in.name,
    #     game_session_id=game_session.id,
    # )

    game_player = GamePlayer.model_validate(
        game_player_in, update={"game_session_id": game_session.id}
    )
    session.add(game_player)
    session.commit()
    session.refresh(game_player)

    return game_player


# make team and add to game session
@router.post("/{game_session_id}/team", response_model=GameTeamPublic)
def create_game_team(
    session: SessionDep,
    game_session_id: str,
    game_team_in: GameTeamCreate,
    current_user: User = Security(get_current_user, scopes=["games:update"]),
):
    """
    Create a new game team.
    """
    # check valid uuid
    try:
        game_session = session.get(GameSession, game_session_id)
    except Exception:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")

    # game_player = GamePlayer(
    #     name=game_player_in.name,
    #     game_session_id=game_session.id,
    # )

    game_team = GameTeam.model_validate(
        game_team_in, update={"game_session_id": game_session.id}
    )
    session.add(game_team)
    session.commit()
    session.refresh(game_team)

    return game_team


# delete game player
@router.delete("/{game_session_id}/player/{game_player_id}")
def delete_game_player(
    session: SessionDep,
    game_session_id: str,
    game_player_id: str,
    current_user: User = Security(get_current_user, scopes=["games:update"]),
):
    """
    Delete a game player.
    """
    # check valid uuid
    try:
        game_session = session.get(GameSession, game_session_id)
    except Exception:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")

    # check valid uuid
    try:
        game_player = session.get(GamePlayer, game_player_id)
    except Exception:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_player:
        raise HTTPException(status_code=404, detail="Game player not found")

    if game_player.game_session_id != game_session.id:
        raise HTTPException(
            status_code=404, detail="Game player not found in this game session"
        )

    session.delete(game_player)
    session.commit()

    return {"success": True}


# delete game team
@router.delete("/{game_session_id}/team/{game_team_id}")
def delete_game_team(
    session: SessionDep,
    game_session_id: str,
    game_team_id: str,
    current_user: User = Security(get_current_user, scopes=["games:update"]),
):
    """
    Delete a game team.
    """
    # check valid uuid
    try:
        game_session = session.get(GameSession, game_session_id)
    except Exception:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")

    # check valid uuid
    try:
        game_team = session.get(GameTeam, game_team_id)
    except Exception:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    if not game_team:
        raise HTTPException(status_code=404, detail="Game team not found")

    if game_team.game_session_id != game_session.id:
        raise HTTPException(
            status_code=404, detail="Game team not found in this game session"
        )

    session.delete(game_team)
    session.commit()

    return {"success": True}


# update game player
@router.patch(
    "/{game_session_id}/player/{game_player_id}", response_model=GamePlayerPublic
)
def update_game_player(
    session: SessionDep,
    game_session_id: str,
    game_player_id: str,
    game_player_in: GamePlayerUpdate,
    current_user: User = Security(get_current_user, scopes=["games:update"]),
):
    """
    Update a game player (e.g., change name).
    """

    # check valid uuid
    try:
        game_session = session.get(GameSession, game_session_id)
    except Exception:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")
    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")
    # check valid uuid
    try:
        game_player = session.get(GamePlayer, game_player_id)
    except Exception:
        # except InvalidTextRepresentation as e:
        raise HTTPException(status_code=400, detail="Invalid UUID")
    if not game_player:
        raise HTTPException(status_code=404, detail="Game player not found")
    if game_player.game_session_id != game_session.id:
        raise HTTPException(
            status_code=404, detail="Game player not found in this game session"
        )
    drink_links = game_player_in.drinks
    # print(drink_links)
    if drink_links:
        # Process each drink link
        for drink_link in drink_links:
            # Check if the drink itself exists
            drink = session.get(Drink, drink_link.drink_id)
            if not drink:
                raise HTTPException(
                    status_code=404,
                    detail=f"Drink with id {drink_link.drink_id} not found",
                )

            # Find if a link already exists between this player and this drink
            statement = select(GamePlayerDrinkLink).where(
                GamePlayerDrinkLink.game_player_id == game_player.id,
                GamePlayerDrinkLink.drink_id == drink_link.drink_id,
            )
            existing_link = session.exec(statement).one_or_none()

            if existing_link:
                if drink_link.amount < 1:
                    # if amount is less than 1 (most likely 0), delete the link
                    session.delete(existing_link)
                    print("Deleting link")
                    continue
                # If the link exists, update its amount
                existing_link.amount = drink_link.amount
                session.add(existing_link)
            else:
                print("Creating new link")
                # If the link does not exist, create a new one
                new_link = GamePlayerDrinkLink(
                    game_player_id=game_player.id,
                    drink_id=drink_link.drink_id,
                    amount=drink_link.amount,
                )
                session.add(new_link)

    # update the game player
    game_player_data = game_player_in.model_dump(exclude_unset=True, exclude={"drinks"})
    game_player.sqlmodel_update(game_player_data)
    session.add(game_player)
    session.commit()
    session.refresh(game_player)
    return game_player


@router.patch(
    "/{game_session_id}/player/{game_player_id}/drink", response_model=GamePlayerPublic
)
def add_drink_to_player(
    background_tasks: BackgroundTasks,
    session: SessionDep,
    game_session_id: str,
    game_player_id: str,
    drink_link_in: GamePlayerDrinkLinkCreate,
    current_user: User = Security(get_current_user, scopes=["games:update"]),
):
    """
    Add a drink to a game player or update the amount if the drink link already exists.
    The amount provided in drink_link_in will be set as the new total amount for that drink.

    """

    # check valid uuid for game_session_id
    try:
        game_session = session.get(GameSession, game_session_id)
    except Exception:
        raise HTTPException(
            status_code=400, detail="Invalid UUID format for game_session_id"
        )

    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")

    # check valid uuid for game_player_id
    try:
        game_player = session.get(GamePlayer, game_player_id)
    except Exception:
        raise HTTPException(
            status_code=400, detail="Invalid UUID format for game_player_id"
        )

    if not game_player:
        raise HTTPException(status_code=404, detail="Game player not found")

    if game_player.game_session_id != game_session.id:
        raise HTTPException(
            status_code=403, detail="Game player not found in this game session"
        )

    # Check if the drink itself exists
    drink = session.get(Drink, drink_link_in.drink_id)
    if not drink:
        raise HTTPException(
            status_code=404, detail=f"Drink with id {drink_link_in.drink_id} not found"
        )

    # Find if a link already exists between this player and this drink
    statement = select(GamePlayerDrinkLink).where(
        GamePlayerDrinkLink.game_player_id == game_player.id,
        GamePlayerDrinkLink.drink_id == drink_link_in.drink_id,
    )
    existing_link = session.exec(statement).one_or_none()

    if existing_link:
        # If the link exists, update its amount
        existing_link.amount += (
            drink_link_in.amount
        )  # Increment the existing amount by the new amount
        if existing_link.amount < 1:
            # If the resulting amount is less than 1, delete the link
            session.delete(existing_link)
            existing_link = None
        session.add(existing_link)
    else:
        # If the link does not exist, create a new one
        new_link = GamePlayerDrinkLink(
            game_player_id=game_player.id,
            drink_id=drink_link_in.drink_id,
            amount=drink_link_in.amount,
        )
        session.add(new_link)

    session.commit()

    # Refresh the game_player instance to load the updated/new drink_links
    session.refresh(game_player)

    # Schedule the broadcast as a background task
    background_tasks.add_task(broadcast_game_update, game_session_id, "drink_added")

    return game_player


# @router.patch("/{game_session_id}/player/{game_player_id}/drink", response_model=GamePlayerPublic)
# def temp_update_game_player(
#     session: SessionDep,
#     game_session_id: str,
#     game_player_id: str,
#     current_user: CurrentUser,
#     drink_link_in: GamePlayerDrinkLinkCreate # Renamed from test_in for clarity
# ):
#     """
#     Add a drink to a game player or update the amount if the drink link already exists.
#     The amount provided in drink_link_in will be set as the new total amount for that drink.
#     """

#     # check valid uuid for game_session_id
#     try:
#         game_session = session.get(GameSession, game_session_id)
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Invalid UUID format for game_session_id")
#     except Exception: # Catch other potential errors from session.get if ID is malformed beyond simple UUID format
#         raise HTTPException(status_code=400, detail="Error processing game_session_id")

#     if not game_session:
#         raise HTTPException(status_code=404, detail="Game session not found")

#     # check valid uuid for game_player_id
#     try:
#         game_player = session.get(GamePlayer, game_player_id)
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Invalid UUID format for game_player_id")
#     except Exception:
#         raise HTTPException(status_code=400, detail="Error processing game_player_id")

#     if not game_player:
#         raise HTTPException(status_code=404, detail="Game player not found")

#     if game_player.game_session_id != game_session.id:
#         raise HTTPException(status_code=403, detail="Game player not found in this game session")

#     # Check if the drink itself exists
#     drink = session.get(Drink, drink_link_in.drink_id)
#     if not drink:
#         raise HTTPException(status_code=404, detail=f"Drink with id {drink_link_in.drink_id} not found")

#     # Find if a link already exists between this player and this drink
#     statement = select(GamePlayerDrinkLink).where(
#         GamePlayerDrinkLink.game_player_id == game_player.id,
#         GamePlayerDrinkLink.drink_id == drink_link_in.drink_id
#     )
#     existing_link = session.exec(statement).one_or_none()

#     if existing_link:
#         # If the link exists, update its amount
#         # Ensure drink_link_in.amount respects constraints (e.g. >= 1 if defined in GamePlayerDrinkLink)
#         existing_link.amount = drink_link_in.amount
#         session.add(existing_link)
#     else:
#         # If the link does not exist, create a new one
#         new_link = GamePlayerDrinkLink(
#             game_player_id=game_player.id,
#             drink_id=drink_link_in.drink_id,
#             amount=drink_link_in.amount
#         )
#         session.add(new_link)

#     session.commit()
#     # Refresh the game_player instance to load the updated/new drink_links
#     # This is important for the response_model=GamePlayerPublic to serialize correctly
#     session.refresh(game_player)
#     # Also refresh related models if their state might have changed and is part of the response
#     # For example, if GamePlayerPublic showed details of the drink that could change.
#     # Here, refreshing game_player should be sufficient for its drink_links.

#     return game_player


# SSE endpoint for real-time updates
@router.get("/{game_session_id}/updates")
async def game_session_updates(game_session_id: str):
    """
    Server-Sent Events endpoint that streams real-time updates for a game session.
    Clients can connect to this endpoint to receive notifications when drinks are added.
    """

    async def event_generator():
        # Create a queue for this client
        queue = asyncio.Queue()

        # Add this client's queue to the subscribers list
        game_session_subscribers[game_session_id].append(queue)

        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'game_session_id': game_session_id})}\n\n"

            # Send periodic heartbeat and listen for updates
            while True:
                try:
                    # Wait for a message with a timeout for heartbeat
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"

        except asyncio.CancelledError:
            # Client disconnected
            pass
        finally:
            # Remove this client's queue from subscribers
            if queue in game_session_subscribers[game_session_id]:
                game_session_subscribers[game_session_id].remove(queue)

            # Clean up empty subscriber lists
            if not game_session_subscribers[game_session_id]:
                del game_session_subscribers[game_session_id]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        },
    )
