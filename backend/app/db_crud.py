import uuid
from typing import Any

from sqlmodel import Session, select

from app.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate, RefreshToken
from hashlib import sha256
from datetime import datetime, timedelta


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate_user(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# Refresh token helpers
def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def store_refresh_token(*, session: Session, user_id: uuid.UUID, token: str, expires_at: datetime) -> RefreshToken:
    rec = RefreshToken(user_id=user_id, token_hash=hash_token(token), expires_at=expires_at)
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec


def get_refresh_token(*, session: Session, token: str) -> RefreshToken | None:
    token_hash = hash_token(token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    return session.exec(stmt).first()


def revoke_refresh_token(*, session: Session, token: str) -> None:
    rec = get_refresh_token(session=session, token=token)
    if rec and rec.revoked_at is None:
        rec.revoked_at = datetime.utcnow()
        session.add(rec)
        session.commit()


def rotate_refresh_token(*, session: Session, old_token: str, new_token: str, new_expires_at: datetime) -> RefreshToken:
    # revoke old
    revoke_refresh_token(session=session, token=old_token)
    # store new
    # Needs user_id; find from old token row
    old = get_refresh_token(session=session, token=old_token)
    # If not found, cannot infer user; caller must handle
    if not old:
        raise ValueError("Old refresh token not found for rotation")
    return store_refresh_token(session=session, user_id=old.user_id, token=new_token, expires_at=new_expires_at)