from collections.abc import Generator
from typing import Annotated
import jwt

from fastapi import Depends, HTTPException, status, Security
from pydantic import ValidationError
from sqlmodel import Session, create_engine, SQLModel
from fastapi.security import (
    OAuth2PasswordBearer,
    SecurityScopes

)
from jwt.exceptions import InvalidTokenError
from app.models import User, TokenData
from app.config import settings
import app.security as security
from app.db import engine
from app.db_crud import get_user_by_email








# def get_db():
#     with Session(engine) as session:
#         yield session

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login/access-token",
    scopes={"me": "Read information about the current user.", "items": "Read items."},
    # auto_error=False,
    )

# SessionDep: Session = Depends(get_db)
# TokenDep: str =  Depends(oauth2_scheme)

SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(security_scopes: SecurityScopes, session: SessionDep, token: TokenDep) -> User:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        email: str = payload.get("sub")
        # print(f"payload: {payload}")
        if email is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(email=email, scopes=token_scopes)
    except (InvalidTokenError, ValidationError) as e:
        print(f"Error: {e}")
        raise credentials_exception
    
    user = get_user_by_email(session=session, email=email)
    if user is None:
        raise credentials_exception
    # user = session.get(User, token_data.sub) # we can access email in the token_data
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")
    # if not user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    # print(security_scopes.scopes)
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    # print(f"User: {user}")
    return user


# CurrentUser = Annotated[User, Depends(get_current_user)]
# CurrentUser = Annotated[User, Security(get_current_user, scopes=["me"])]
CurrentUser = Annotated[User, Security(get_current_user)]



async def get_current_active_user(
    current_user: Annotated[User, Security(get_current_user)],
    # current_user: Annotated[User, Security(get_current_user, scopes=["me"])],
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# def get_current_active_superuser(current_user: CurrentUser) -> User:
#     if not current_user.is_superuser:
#         raise HTTPException(
#             status_code=403, detail="The user doesn't have enough privileges"
#         )
#     return current_user


