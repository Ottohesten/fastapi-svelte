from __future__ import annotations
from typing import Dict, Set
from fastapi import WebSocket
import asyncio
from sqlmodel import Session as SQLModelSession

def serialize_game_session(game_session) -> dict:
    return {
        "id": str(game_session.id),
        "title": game_session.title,
        "players": [
            {
                "id": str(p.id),
                "name": p.name,
                "team_id": str(p.team_id) if p.team_id else None,
                "drinks": [
                    {
                        "drink_id": str(dl.drink_id),
                        "drink_name": dl.drink.name if dl.drink else None,
                        "amount": dl.amount,
                    }
                    for dl in (p.drink_links or [])
                ],
            }
            for p in (game_session.players or [])
        ],
        "teams": [
            {
                "id": str(t.id),
                "name": t.name,
                "player_ids": [str(pl.id) for pl in (t.players or [])],
            }
            for t in (game_session.teams or [])
        ],
    }

class GameSessionConnectionManager:
    """Manages WebSocket connections per game session.

    - Each game_session_id maps to a set of active WebSocket connections.
    - Provides broadcast utilities with per-connection error isolation.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, game_session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._sessions.setdefault(game_session_id, set()).add(websocket)

    async def disconnect(self, game_session_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            conns = self._sessions.get(game_session_id)
            if not conns:
                return
            conns.discard(websocket)
            if not conns:
                # cleanup empty set
                self._sessions.pop(game_session_id, None)

    async def broadcast_json(self, game_session_id: str, message: dict) -> None:
        async with self._lock:
            conns = list(self._sessions.get(game_session_id, set()))
        if not conns:
            return
        to_remove: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                to_remove.append(ws)
        if to_remove:
            async with self._lock:
                live_set = self._sessions.get(game_session_id)
                if live_set:
                    for ws in to_remove:
                        live_set.discard(ws)
                    if not live_set:
                        self._sessions.pop(game_session_id, None)

    def active_counts(self) -> dict[str, int]:
        return {k: len(v) for k, v in self._sessions.items()}


manager = GameSessionConnectionManager()


def broadcast_game_session_state(session: SQLModelSession, game_session_id: str):
    from app.models import GameSession as GS
    instance = session.get(GS, game_session_id)
    if not instance:
        return
    payload = serialize_game_session(instance)
    async def _broadcast():
        await manager.broadcast_json(game_session_id, {"type": "update", "data": payload})
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_broadcast())
    except RuntimeError:
        import anyio
        anyio.run(_broadcast)
