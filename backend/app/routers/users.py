import uuid
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Security, status
from sqlmodel import func, select

import app.db_crud as db_crud
from app.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_user,
    get_current_user,
)
from app.config import settings
from app.security import get_password_hash, verify_password
from app.models import (
    HTTPExceptionDetail,
    Message,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserMePublic,
    Role,
    RolePublic,
    UserWithPermissionsPublic,
    UsersWithPermissionsPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.permissions import get_user_effective_scopes
from app.utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=UsersPublic)
def get_users(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Security(get_current_user, scopes=["users:read"]),
):
    """
    Retrieve users.
    """

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).order_by(User.email).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(
        data=[UserPublic.model_validate(user) for user in users], count=count
    )


@router.get("/with-permissions", response_model=UsersWithPermissionsPublic)
def get_users_with_permissions(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Security(get_current_user),
):
    """
    Retrieve users including their roles, custom_scopes and computed effective_scopes.
    """
    # Require superuser privileges for this consolidated permissions view
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).order_by(User.email).offset(skip).limit(limit)
    users = session.exec(statement).all()

    data: list[UserWithPermissionsPublic] = []
    for u in users:
        roles_public = [
            # Create RolePublic instances explicitly
            RolePublic(
                id=r.id, name=r.name, description=r.description, scopes=r.scopes or []
            )
            for r in (u.roles or [])
        ]
        effective = sorted(list(get_user_effective_scopes(u)))
        data.append(
            UserWithPermissionsPublic(
                id=u.id,
                email=u.email,
                is_active=u.is_active,
                is_superuser=u.is_superuser,
                full_name=u.full_name,
                roles=roles_public,
                custom_scopes=u.custom_scopes or [],
                effective_scopes=effective,
            )
        )

    return UsersWithPermissionsPublic(data=data, count=count)


@router.post("/", response_model=UserPublic)
def create_user(
    *,
    session: SessionDep,
    user_in: UserCreate,
    current_user: User = Security(get_current_user, scopes=["users:create"]),
):
    """
    Create new user.
    """
    user = db_crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists",
        )

    user = db_crud.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
):
    """
    Update own user.
    """

    if user_in.email:
        existing_user = db_crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
):
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.get(
    "/me",
    response_model=UserMePublic,
    responses={
        401: {
            # "content": {"application/json": {"example": {"detail": "Not authenticated"}}},
            "model": HTTPExceptionDetail
        }
    },
)
def get_user_me(*, current_user: Annotated[User, Security(get_current_active_user)]):
    """
    Get current user.
    """
    scopes = sorted(list(get_user_effective_scopes(current_user)))
    return UserMePublic(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        full_name=current_user.full_name,
        scopes=scopes,
    )


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Message:
    """
    Delete own user.
    """
    # Prevent superusers from deleting themselves to avoid system lockout
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super users are not allowed to delete themselves",
        )
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister):
    """
    Create new user without the need to be logged in.
    """
    user = db_crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists",
        )
    user_create = UserCreate.model_validate(user_in)
    user = db_crud.create_user(session=session, user_create=user_create)
    return user


@router.get("/{user_id}", response_model=UserPublic)
def get_user(
    user_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get a specific user by id.
    """
    user = session.get(User, user_id)
    if user == current_user:
        return user
    # Users with users:read scope can access any user
    if "users:read" not in get_user_effective_scopes(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch("/{user_id}", response_model=UserPublic)
def update_user(
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
    current_user: User = Security(get_current_user, scopes=["users:update"]),
):
    """
    Update a user.
    """

    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="A user with this id does not exist",
        )

    if user_in.email:
        existing_user = db_crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != db_user.id:
            raise HTTPException(
                status_code=409, detail="A user with this email already exists"
            )

    db_user = db_crud.update_user(
        session=session,
        db_user=db_user,
        user_in=user_in,
    )

    return db_user


@router.delete("/{user_id}")
def delete_user(
    session: SessionDep,
    user_id: uuid.UUID,
    current_user: User = Security(get_current_user, scopes=["users:delete"]),
) -> Message:
    """
    Delete a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404, detail="A user with this id does not exist"
        )
    if user == current_user:
        raise HTTPException(status_code=403, detail="Users cannot delete themselves")
    session.delete(user)
    session.commit()
    return Message(message="User deleted successfully")


##########################################################################
# Roles segmentt

# permissions_router = APIRouter(prefix="", tags=["user-permissions"])
permissions_router = APIRouter(prefix="/{user_id}", tags=["user-permissions"])


# @router.post("/{user_id}/roles/{role_id}", response_model=UserPublic)
@permissions_router.post("/roles/{role_id}", response_model=UserPublic)
def assign_role_to_user(
    session: SessionDep,
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    current_user: User = Security(get_current_user, scopes=["users:update"]),
):
    """
    Assign a role to a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="A user with this id does not exist",
        )
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=404,
            detail="A role with this id does not exist",
        )
    if role not in user.roles:
        user.roles.append(role)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


@permissions_router.delete("/roles/{role_id}", response_model=UserPublic)
def remove_role_from_user(
    session: SessionDep,
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    current_user: User = Security(get_current_user, scopes=["users:update"]),
):
    """
    Remove a role from a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="A user with this id does not exist",
        )
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=404,
            detail="A role with this id does not exist",
        )
    if role in user.roles:
        user.roles.remove(role)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


@permissions_router.post("/scopes", response_model=UserPublic)
def assign_scopes_to_user(
    session: SessionDep,
    user_id: uuid.UUID,
    scopes: list[str],
    current_user: User = Security(get_current_user, scopes=["users:update"]),
):
    """
    Assign custom scopes to a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="A user with this id does not exist",
        )

    # Create a copy of the list to ensure SQLAlchemy detects the change
    current_scopes = list(user.custom_scopes) if user.custom_scopes else []
    modified = False

    for scope in scopes:
        if scope not in current_scopes:
            current_scopes.append(scope)
            modified = True

    if modified:
        user.custom_scopes = current_scopes
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


@permissions_router.delete("/scopes", response_model=UserPublic)
def remove_scopes_from_user(
    session: SessionDep,
    user_id: uuid.UUID,
    scopes: list[str],
    current_user: User = Security(get_current_user, scopes=["users:update"]),
):
    """
    Remove custom scopes from a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="A user with this id does not exist",
        )

    # Create a copy of the list to ensure SQLAlchemy detects the change
    current_scopes = list(user.custom_scopes) if user.custom_scopes else []
    modified = False

    for scope in scopes:
        if scope in current_scopes:
            current_scopes.remove(scope)
            modified = True

    if modified:
        user.custom_scopes = current_scopes
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


# This line should always be at the end of the file
router.include_router(permissions_router)
