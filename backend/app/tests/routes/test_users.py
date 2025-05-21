import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import db_crud
from app.config import settings
from app.security import verify_password
from app.models import (
    User,
    UserCreate
)
from app.tests.utils.utils import (
    random_email,
    random_lower_string,
)





def test_get_users_superuser_me(client: TestClient, superuser_token_headers: dict[str, str]):
    """
    Test the /users/me endpoint for superuser
    """
    r = client.get(f"/users/me", headers=superuser_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"]
    assert current_user["email"] == settings.FIRST_SUPERUSER


def test_get_users_normal_user_me(client: TestClient, normal_user_token_headers: dict[str, str]):
    """
    Test the /users/me endpoint for normal user
    """
    r = client.get(f"/users/me", headers=normal_user_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is False
    assert current_user["email"] == settings.EMAIL_TEST_USER



def test_get_existing_user(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/{user_id} endpoint for superuser
    """
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = db_crud.create_user(session=db, user_create=user_in)
    user_id = user.id

    r = client.get(f"/users/{user_id}", headers=superuser_token_headers)

    assert 200 <= r.status_code < 300
    api_user = r.json()
    existing_user = db_crud.get_user_by_email(session=db, email=username)
    assert existing_user
    assert existing_user.email == api_user["email"]


def test_get_existing_user_permissions_error(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    """
    Test the /users/{user_id} endpoint for normal user

    Should return 403 forbidden error
    """
    r = client.get(
        f"/users/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "The user doesn't have enough privileges"}


def test_get_existing_user_current_user(client: TestClient, db: Session):
    """
    Test the /users/{user_id} endpoint for current user
    """
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = db_crud.create_user(session=db, user_create=user_in)
    user_id = user.id

    login_data = {
        "username": username,
        "password": password,
    }

    r = client.post(f"/login/access-token", data=login_data)

    tokens = r.json()
    access_token = tokens["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}

    r = client.get(f"/users/{user_id}", headers=headers)
    assert 200 <= r.status_code < 300

    api_user = r.json()
    existing_user = db_crud.get_user_by_email(session=db, email=username)
    assert existing_user
    assert existing_user.email == api_user["email"]


def test_create_user_existing_username(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/ endpoint for superuser
    """
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    db_crud.create_user(session=db, user_create=user_in)

    data = {"email": username, "password": password}
    r = client.post(
        f"/users/",
        headers=superuser_token_headers,
        json=data,
    )
    created_user = r.json()

    assert r.status_code == 400
    assert "_id" not in created_user
    assert r.json()["detail"] == "A user with this email already exists"


def test_create_user_existing_username_2(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/ endpoint for normal user
    """

    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    db_crud.create_user(session=db, user_create=user_in)
    
    data = {"email": username, "password": password}
    r = client.post(
        f"/users/",
        headers=normal_user_token_headers,
        json=data,
    )

    created_user = r.json()
    assert r.status_code == 403
    assert "_id" not in created_user
    assert r.json() == {"detail": "The user doesn't have enough privileges"}


def test_create_user_by_normal_user(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/ endpoint for normal user
    """

    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password}
    r = client.post(
        f"/users/",
        headers=normal_user_token_headers,
        json=data,
    )

    created_user = r.json()
    assert r.status_code == 403
    assert "_id" not in created_user
    assert r.json() == {"detail": "The user doesn't have enough privileges"}



def test_create_user_new_email(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    # with (
    #     patch("app.utils.send_email", return_value=None),
    #     patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
    #     patch("app.core.config.settings.SMTP_USER", "admin@example.com"),
    # ):
        username = random_email()
        password = random_lower_string()
        data = {"email": username, "password": password}
        r = client.post(
            f"/users/",
            headers=superuser_token_headers,
            json=data,
        )
        assert 200 <= r.status_code < 300
        created_user = r.json()
        user = db_crud.get_user_by_email(session=db, email=username)
        assert user
        assert user.email == created_user["email"]
        assert verify_password(password, user.hashed_password)


def test_get_users_by_superuser(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/ endpoint for superuser
    """
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    db_crud.create_user(session=db, user_create=user_in)

    username_2 = random_email()
    password_2 = random_lower_string()
    user_in_2 = UserCreate(email=username_2, password=password_2)
    db_crud.create_user(session=db, user_create=user_in_2)
    
    r = client.get(
        f"/users/",
        headers=superuser_token_headers,
    )

    assert 200 <= r.status_code < 300
    all_users = r.json()
    assert len(all_users) > 1
    assert "count" in all_users
    for user in all_users["data"]:
        assert "email" in user



def test_get_users_by_normal_user(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/ endpoint for normal user
    """
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    db_crud.create_user(session=db, user_create=user_in)

    r = client.get(
        f"/users/",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403
    assert r.json() == {"detail": "The user doesn't have enough privileges"}



def test_update_user_me_by_normal_user(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/me endpoint for superuser
    """
    username = random_email()
    full_name = "Updated Name"
    data = {"full_name": full_name, "email": username}
    
    r = client.patch(
        f"/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert 200 <= r.status_code < 300
    updated_user = r.json()
    assert updated_user["email"] == username
    assert updated_user["full_name"] == full_name

    user_query = select(User).where(User.email == username)
    user_db = db.exec(user_query).first()
    assert user_db
    assert user_db.email == updated_user["email"]
    assert user_db.full_name == updated_user["full_name"]



def test_update_user_me_by_superuser(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/me endpoint for superuser
    """
    username = random_email()
    full_name = "Updated Name"
    data = {"full_name": full_name, "email": username}
    
    r = client.patch(
        f"/users/me",
        headers=superuser_token_headers,
        json=data,
    )
    assert 200 <= r.status_code < 300
    updated_user = r.json()
    assert updated_user["email"] == username
    assert updated_user["full_name"] == full_name

    user_query = select(User).where(User.email == username)
    user_db = db.exec(user_query).first()
    assert user_db
    assert user_db.email == updated_user["email"]
    assert user_db.full_name == updated_user["full_name"]


def test_update_password_me(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/me endpoint for superuser
    """
    new_password = random_lower_string()
    data = {
        "current_password": settings.FIRST_SUPERUSER_PASSWORD,
        "new_password": new_password,
    }
    r = client.patch(
        f"/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert 200 <= r.status_code < 300
    updated_user = r.json()
    assert updated_user["message"] == "Password updated successfully"

    user_query = select(User).where(User.email == settings.FIRST_SUPERUSER)
    user_db = db.exec(user_query).first()
    assert user_db
    assert user_db.email == settings.FIRST_SUPERUSER
    assert verify_password(new_password, user_db.hashed_password)


def test_update_password_me_incorrect_current_password(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/me endpoint for superuser
    """
    new_password = random_lower_string()
    data = {
        "current_password": "incorrect_password",
        "new_password": new_password,
    }
    r = client.patch(
        f"/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 400
    updated_user = r.json()
    assert updated_user["detail"] == "Incorrect password"


def test_update_user_me_email_exists_by_normal_user(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    """
    test the users/me endpoint for normal user
    """
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = db_crud.create_user(session=db, user_create=user_in)
    
    data = {"email": username}
    r = client.patch(
        f"/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "User with this email already exists"


def test_update_user_me_email_exists_by_superuser(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    test the users/me endpoint for superuser
    """
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = db_crud.create_user(session=db, user_create=user_in)
    
    data = {"email": username}
    r = client.patch(
        f"/users/me",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "User with this email already exists"



def test_update_user_me_same_password_error(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    test the users/me endpoint for superuser when using the same password
    """
    data = {
        "current_password": settings.FIRST_SUPERUSER_PASSWORD,
        "new_password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.patch(
        f"/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 400
    updated_user = r.json()
    assert updated_user["detail"] == "New password cannot be the same as the current one"



def test_register_user(client: TestClient, db: Session) -> None:
    """
    Test the /signup/ endpoint for registering a new user
    """
    username = random_email()
    password = random_lower_string()
    full_name = random_lower_string()
    data = {"email": username, "password": password, "full_name": full_name}
    r = client.post(
        f"/users/signup",
        json=data,
    )
    assert r.status_code == 200
    created_user = r.json()
    assert created_user["email"] == username
    assert created_user["full_name"] == full_name

    user_query = select(User).where(User.email == username)
    user_db = db.exec(user_query).first()
    assert user_db
    assert user_db.email == username
    assert user_db.full_name == full_name
    assert verify_password(password, user_db.hashed_password)


def test_register_user_already_exists_error(client: TestClient, db: Session) -> None:
    """
    Test the /signup/ endpoint for registering a new user which already exists
    """
    password = random_lower_string()
    full_name = random_lower_string()
    data = {"email": settings.FIRST_SUPERUSER, "password": password, "full_name": full_name}
    r = client.post(
        f"/users/signup",
        json=data,
    )
    assert r.status_code == 400
    created_user = r.json()
    assert created_user["detail"] == "A user with this email already exists"


def test_update_user_by_superuser(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/{user_id} endpoint for superuser
    """
    username = random_email()
    password = random_lower_string()

    user_in = UserCreate(email=username, password=password)
    user = db_crud.create_user(session=db, user_create=user_in)


    new_email = random_email()
    full_name = "Updated name"
    data = {"full_name": full_name, "email": new_email}

    db_query = select(User).where(User.id == user.id)
    user = db.exec(db_query).first()
    r = client.patch(
        f"/users/{user.id}", # type: ignore
        headers=superuser_token_headers,
        json=data,
    )
    assert 200 <= r.status_code < 300
    updated_user = r.json()
    assert updated_user["email"] == new_email
    assert updated_user["full_name"] == full_name 

    user_db = db.get(User, user.id) # type: ignore
    db.refresh(user_db) # this is needed to get the updated user
    assert user_db
    assert user_db.email == updated_user["email"]
    assert user_db.full_name == full_name


def test_update_user_by_normal_user(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/{user_id} endpoint for normal user
    """
    username = random_email()
    password = random_lower_string()

    user_in = UserCreate(email=username, password=password)
    user = db_crud.create_user(session=db, user_create=user_in)


    new_email = random_email()
    full_name = "Updated name"
    data = {"full_name": full_name, "email": new_email}

    db_query = select(User).where(User.id == user.id)
    user = db.exec(db_query).first()
    r = client.patch(
        f"/users/{user.id}", # type: ignore
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "The user doesn't have enough privileges"



def test_update_user_by_superuser_not_exists(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/{user_id} endpoint for superuser where 
    """
    username = random_email()
    password = random_lower_string()

    user_in = UserCreate(email=username, password=password)
    user = db_crud.create_user(session=db, user_create=user_in)


    new_email = random_email()
    full_name = "Updated name"
    data = {"full_name": full_name, "email": new_email}

    r = client.patch(
        f"/users/{uuid.uuid4()}", # type: ignore
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "A user with this id does not exist"



def test_update_user_by_superuser_email_exists(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/{user_id} endpoint for superuser where email already exists
    """
    username = random_email()
    password = random_lower_string()

    user_in = UserCreate(email=username, password=password)
    user = db_crud.create_user(session=db, user_create=user_in)

    username_2 = random_email()
    password_2 = random_lower_string()

    user_in_2 = UserCreate(email=username_2, password=password_2)
    user_2 = db_crud.create_user(session=db, user_create=user_in_2)

    data = {"email": username_2}

    db_query = select(User).where(User.id == user.id)
    user = db.exec(db_query).first()
    r = client.patch(
        f"/users/{user.id}", # type: ignore
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "A user with this email already exists"


def test_delete_user_me(client: TestClient, db: Session):
    """
    Test the users/me endpoint for deleting a user
    """

    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = db_crud.create_user(session=db, user_create=user_in)

    login_data = {
        "username": username,
        "password": password,
    }

    r = client.post(f"/login/access-token", data=login_data)

    tokens = r.json()
    access_token = tokens["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}

    r = client.delete(f"/users/me", headers=headers)
    assert 200 <= r.status_code < 300
    deleted_user = r.json()
    assert deleted_user["message"] == "User deleted successfully"

    user_query = select(User).where(User.email == username)
    user_db = db.exec(user_query).first()
    assert user_db is None


def test_delete_user_me_by_superuser(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/me endpoint for superuser
    """
    r = client.delete(f"/users/me", headers=superuser_token_headers)
    assert r.status_code == 403
    assert r.json()["detail"] == "Super users are not allowed to delete themselves"


def test_delete_user_by_superuser(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/{user_id} endpoint for superuser
    """
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = db_crud.create_user(session=db, user_create=user_in)

    r = client.delete(
        f"/users/{user.id}", # type: ignore
        headers=superuser_token_headers,
    )
    assert 200 <= r.status_code < 300
    deleted_user = r.json()
    assert deleted_user["message"] == "User deleted successfully"

    user_query = select(User).where(User.email == username)
    user_db = db.exec(user_query).first()
    assert user_db is None

def test_delete_user_by_superuser_not_exists(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/{user_id} endpoint for superuser where user does not exist
    """
    r = client.delete(
        f"/users/{uuid.uuid4()}", # type: ignore
        headers=superuser_token_headers,
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "A user with this id does not exist"


def test_delete_user_by_normal_user(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/{user_id} endpoint for normal user
    """
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = db_crud.create_user(session=db, user_create=user_in)

    r = client.delete(
        f"/users/{user.id}", # type: ignore
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "The user doesn't have enough privileges"

def test_delete_user_current_user_superuser(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    """
    Test the /users/{user_id} endpoint for superuser and try to delete itself
    """
    user = db_crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user

    r = client.delete(
        f"/users/{user.id}", # type: ignore
        headers=superuser_token_headers,
    )

    assert r.status_code == 403
    assert r.json()["detail"] == "Super users are not allowed to delete themselves"