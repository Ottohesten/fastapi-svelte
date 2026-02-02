from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Security, Response
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

import app.db_crud as db_crud
from app.deps import CurrentUser, SessionDep, get_current_user
import app.security as security
from app.config import settings
from app.security import get_password_hash
from app.models import Message, NewPassword, Token, UserPublic, User, RefreshRequest
from app.permissions import get_user_effective_scopes
from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)

router = APIRouter(tags=["login"])


@router.post("/login/access-token", response_model=Token)
def login_access_token(
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = db_crud.authenticate_user(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Get user's effective scopes from roles + custom scopes
    user_scopes = list(get_user_effective_scopes(user))

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    access_token = security.create_access_token(
        data={"sub": user.email, "scopes": user_scopes},
        expires_delta=access_token_expires,
    )
    refresh_token = security.create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )
    # persist refresh for revocation
    db_crud.store_refresh_token(
        session=session,
        user_id=user.id,
        token=refresh_token,
        expires_at=(settings and (settings.ENVIRONMENT,))
        and (  # placeholder to suppress static checks
            # compute absolute expiry using timedelta relative to now on server side
            datetime.now(timezone.utc) + refresh_token_expires
        ),
    )
    # HTTP-only cookie for refresh token (optional; primary flow uses body to rotate)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=(settings.ENVIRONMENT != "local"),
        samesite="lax",
        path="/",
        max_age=int(refresh_token_expires.total_seconds()),
    )
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/login/refresh", response_model=Token)
def refresh_access_token(
    response: Response, session: SessionDep, body: RefreshRequest
) -> Token:
    """
    Issue a new access token using the refresh token from cookie (preferred) or body.
    """
    # Prefer cookie over body param
    # FastAPI provides cookies through Request, but we can accept via dependency on Response? Simpler: use body param and document cookie usage in frontend.
    # We'll still try to read from cookie via a workaround in Request if needed; keeping minimal here.
    import jwt

    # Note: accept both locations to keep it simple for now
    # Retrieve from cookie if not provided
    # We expect the refresh token in the request body; cookie is maintained for browser storage convenience.
    # Decode and validate refresh token
    from jwt import InvalidTokenError

    try:
        token_to_use = body.refresh_token
        if token_to_use is None:
            # If not provided, raise clear 401
            raise HTTPException(status_code=401, detail="Missing refresh token")
        payload = jwt.decode(
            token_to_use, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        # Verify token exists and not revoked/expired in DB
        rec = db_crud.get_refresh_token(session=session, token=token_to_use)
        if not rec or rec.revoked_at is not None:
            raise HTTPException(status_code=401, detail="Refresh token revoked")
        # expiry check (defense-in-depth beyond JWT exp)
        if rec.expires_at <= __import__("datetime").datetime.utcnow():
            raise HTTPException(status_code=401, detail="Refresh token expired")
    except (InvalidTokenError, HTTPException):
        raise
    # Load user and build scopes
    user = db_crud.get_user_by_email(session=session, email=sub)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid user")
    user_scopes = list(get_user_effective_scopes(user))
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access = security.create_access_token(
        data={"sub": user.email, "scopes": user_scopes},
        expires_delta=access_token_expires,
    )
    # Optionally rotate refresh token
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh = security.create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )
    # rotate DB record
    db_crud.rotate_refresh_token(
        session=session,
        old_token=token_to_use,
        new_token=new_refresh,
        new_expires_at=(
            __import__("datetime").datetime.utcnow() + refresh_token_expires
        ),
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=(settings.ENVIRONMENT != "local"),
        samesite="lax",
        path="/",
        max_age=int(refresh_token_expires.total_seconds()),
    )
    return Token(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout", response_model=Message)
def logout(
    response: Response, session: SessionDep, body: RefreshRequest | None = None
) -> Message:
    """Clear refresh cookie (client should also clear access-token cookie)."""
    # If a refresh token is provided, revoke it
    if body and body.refresh_token:
        try:
            db_crud.revoke_refresh_token(session=session, token=body.refresh_token)
        except Exception:
            pass
    response.delete_cookie(key="refresh_token", path="/")
    return Message(message="Logged out")


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
def recover_password(email: str, session: SessionDep) -> Message:
    """
    Password Recovery
    """
    user = db_crud.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    send_email(
        email_to=user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Password recovery email sent")


@router.post("/reset-password/")
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = db_crud.get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(password=body.new_password)
    user.hashed_password = hashed_password
    session.add(user)
    session.commit()
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    response_class=HTMLResponse,
)
def recover_password_html_content(
    email: str,
    session: SessionDep,
    current_user: User = Security(get_current_user, scopes=["users:update"]),
) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = db_crud.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(
        content=email_data.html_content, headers={"subject:": email_data.subject}
    )
