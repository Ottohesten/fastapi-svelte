import asyncio
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import db_crud
from app.models import UserCreate
from app.routers.game import broadcast_game_update, game_session_subscribers
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


def _create_game(
    client: TestClient,
    headers: dict[str, str],
    *,
    title: str = "Friday game",
    teams: list[dict[str, str]] | None = None,
) -> dict:
    response = client.post(
        "/game/",
        headers=headers,
        json={"title": title, "teams": teams},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _create_player(
    client: TestClient,
    headers: dict[str, str],
    game_id: str,
    *,
    name: str = "Alice",
    team_id: str | None = None,
) -> dict:
    response = client.post(
        f"/game/{game_id}/player",
        headers=headers,
        json={"name": name, "team_id": team_id},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _headers_with_scopes(
    client: TestClient, db: Session, scopes: list[str]
) -> dict[str, str]:
    password = random_lower_string()
    user = db_crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=password),
    )
    user.custom_scopes = scopes
    db.add(user)
    db.commit()
    return user_authentication_headers(
        client=client,
        email=user.email,
        password=password,
    )


def test_drink_crud(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    create_response = client.post(
        "/game/drinks",
        headers=superuser_token_headers,
        json={"name": "Water"},
    )
    assert create_response.status_code == 200
    drink = create_response.json()

    list_response = client.get("/game/drinks")
    assert list_response.status_code == 200
    assert drink["id"] in {item["id"] for item in list_response.json()}

    update_response = client.patch(
        f"/game/drinks/{drink['id']}",
        headers=superuser_token_headers,
        json={"name": "Sparkling water"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Sparkling water"

    delete_response = client.delete(
        f"/game/drinks/{drink['id']}", headers=superuser_token_headers
    )
    assert delete_response.status_code == 200
    assert delete_response.json() == {"success": True}


def test_drink_mutations_require_scopes(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.post(
        "/game/drinks",
        headers=normal_user_token_headers,
        json={"name": "Forbidden drink"},
    )
    assert response.status_code == 403


def test_update_and_delete_missing_drink(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    missing_id = uuid4()
    update_response = client.patch(
        f"/game/drinks/{missing_id}",
        headers=superuser_token_headers,
        json={"name": "Missing"},
    )
    assert update_response.status_code == 404


def test_game_session_crud_and_nested_teams(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    game = _create_game(
        client,
        superuser_token_headers,
        teams=[{"name": "Red"}, {"name": "Blue"}],
    )
    assert {team["name"] for team in game["teams"]} == {"Red", "Blue"}

    get_response = client.get(f"/game/{game['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Friday game"

    list_response = client.get("/game/")
    assert list_response.status_code == 200
    assert game["id"] in {item["id"] for item in list_response.json()}

    delete_response = client.delete(
        f"/game/{game['id']}", headers=superuser_token_headers
    )
    assert delete_response.status_code == 200
    assert delete_response.json() == {"success": True}


def test_game_creation_requires_scope(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.post(
        "/game/",
        headers=normal_user_token_headers,
        json={"title": "Forbidden", "teams": None},
    )
    assert response.status_code == 403


def test_scoped_owner_can_create_and_delete_game(
    client: TestClient, db: Session
) -> None:
    headers = _headers_with_scopes(client, db, ["games:create"])
    game = _create_game(client, headers, title="Owned game")

    response = client.delete(f"/game/{game['id']}", headers=headers)
    assert response.status_code == 200


def test_unrelated_user_cannot_delete_game(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    game = _create_game(client, superuser_token_headers)

    response = client.delete(f"/game/{game['id']}", headers=normal_user_token_headers)
    assert response.status_code == 403


def test_get_missing_and_invalid_game(client: TestClient) -> None:
    missing_response = client.get(f"/game/{uuid4()}")
    assert missing_response.status_code == 404

    invalid_response = client.get("/game/not-a-uuid")
    assert invalid_response.status_code == 400


def test_team_and_player_lifecycle(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    game = _create_game(client, superuser_token_headers)
    team_response = client.post(
        f"/game/{game['id']}/team",
        headers=superuser_token_headers,
        json={"name": "Green"},
    )
    assert team_response.status_code == 200
    team = team_response.json()

    player = _create_player(
        client,
        superuser_token_headers,
        game["id"],
        team_id=team["id"],
    )
    assert player["team_id"] == team["id"]

    update_response = client.patch(
        f"/game/{game['id']}/player/{player['id']}",
        headers=superuser_token_headers,
        json={"name": "Alice updated", "team_id": team["id"]},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Alice updated"

    delete_player_response = client.delete(
        f"/game/{game['id']}/player/{player['id']}",
        headers=superuser_token_headers,
    )
    assert delete_player_response.status_code == 200

    delete_team_response = client.delete(
        f"/game/{game['id']}/team/{team['id']}",
        headers=superuser_token_headers,
    )
    assert delete_team_response.status_code == 200


def test_player_from_another_session_is_rejected(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    first_game = _create_game(client, superuser_token_headers, title="First")
    second_game = _create_game(client, superuser_token_headers, title="Second")
    player = _create_player(client, superuser_token_headers, first_game["id"])

    response = client.delete(
        f"/game/{second_game['id']}/player/{player['id']}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_player_drink_links_can_be_created_updated_and_removed(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    game = _create_game(client, superuser_token_headers)
    player = _create_player(client, superuser_token_headers, game["id"])
    drink_response = client.post(
        "/game/drinks",
        headers=superuser_token_headers,
        json={"name": "Juice"},
    )
    drink = drink_response.json()

    add_response = client.patch(
        f"/game/{game['id']}/player/{player['id']}",
        headers=superuser_token_headers,
        json={
            "name": "Alice",
            "drinks": [{"drink_id": drink["id"], "amount": 2}],
        },
    )
    assert add_response.status_code == 200
    assert add_response.json()["drink_links"][0]["amount"] == 2

    update_response = client.patch(
        f"/game/{game['id']}/player/{player['id']}",
        headers=superuser_token_headers,
        json={
            "name": "Alice",
            "drinks": [{"drink_id": drink["id"], "amount": 3}],
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["drink_links"][0]["amount"] == 3

    remove_response = client.patch(
        f"/game/{game['id']}/player/{player['id']}",
        headers=superuser_token_headers,
        json={
            "name": "Alice",
            "drinks": [{"drink_id": drink["id"], "amount": 0}],
        },
    )
    assert remove_response.status_code == 200
    assert remove_response.json()["drink_links"] == []


def test_player_drink_endpoint_increments_amount(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    game = _create_game(client, superuser_token_headers)
    player = _create_player(client, superuser_token_headers, game["id"])
    drink = client.post(
        "/game/drinks",
        headers=superuser_token_headers,
        json={"name": "Soda"},
    ).json()
    url = f"/game/{game['id']}/player/{player['id']}/drink"

    first_response = client.patch(
        url,
        headers=superuser_token_headers,
        json={"drink_id": drink["id"], "amount": 1},
    )
    assert first_response.status_code == 200

    second_response = client.patch(
        url,
        headers=superuser_token_headers,
        json={"drink_id": drink["id"], "amount": 2},
    )
    assert second_response.status_code == 200
    assert second_response.json()["drink_links"][0]["amount"] == 3


def test_player_update_rejects_unknown_drink(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    game = _create_game(client, superuser_token_headers)
    player = _create_player(client, superuser_token_headers, game["id"])

    response = client.patch(
        f"/game/{game['id']}/player/{player['id']}",
        headers=superuser_token_headers,
        json={
            "name": "Alice",
            "drinks": [{"drink_id": str(uuid4()), "amount": 1}],
        },
    )
    assert response.status_code == 404


def test_broadcast_game_update_notifies_subscribers() -> None:
    game_id = str(uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    game_session_subscribers[game_id].append(queue)
    try:
        asyncio.run(broadcast_game_update(game_id, "drink_added"))
        message = queue.get_nowait()
        assert message["type"] == "drink_added"
        assert message["game_session_id"] == game_id
        assert "timestamp" in message
    finally:
        game_session_subscribers.pop(game_id, None)
