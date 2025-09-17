# Realtime Game Session Updates

This application now supports realtime scoreboard updates for game sessions via WebSockets.

## Backend

Endpoint: `GET /game/{id}` still returns the canonical session state.
WebSocket: `WS /ws/game/{game_session_id}`

On connect:
1. Server accepts anonymous connection.
2. Sends a `{"type":"snapshot","data": GameRealtimeSnapshot}` payload containing the full current state.
3. Client remains subscribed for incremental `{"type":"update", ...}` messages whenever a mutation occurs.

### Broadcast Flow
Mutation endpoints (create/update/delete team/player, drinks adjustments, session lifecycle) call `broadcast_game_session_state()` after committing changes. That helper re-serializes the authoritative database row and schedules an async broadcast to all connected clients for that session id.

### Serialization
A lightweight serializer in `app/realtime.py` produces a minimal JSON shape (ids, names, relationships, drink amounts) to reduce payload size and avoid Pydantic overhead.

## Frontend
The page `src/routes/game/[game_session_id]/+page.svelte` now:
- Performs SSR load of initial `game_session` (forms + snapshot) via existing load function.
- Opens a WebSocket on mount to the backend; updates local `gameSession` state on `snapshot` and `update` messages.
- Falls back to a simple reload retry after a 3s delay if the socket closes unexpectedly.

Types are defined in `src/lib/types/game-realtime.ts` for the broadcast message structures.

## Future Enhancements
- Authenticated write channel or role-based filtering.
- Backoff with jitter instead of single reload.
- Differential (patch) updates instead of full snapshots.
- Presence / connection counts endpoint (use `manager.active_counts()`).
- Graceful handling if backend host differs from frontend (currently naive port substitution to :8000).

## Message Contracts
```
{ "type": "snapshot" | "update", "data": GameRealtimeSnapshot }
{ "type": "error", "detail": string }
```

`GameRealtimeSnapshot` fields:
```
{
  id: string,
  title: string,
  players: [{ id, name, team_id, drinks: [{ drink_id, drink_name, amount }] }],
  teams: [{ id, name, player_ids: string[] }]
}
```
