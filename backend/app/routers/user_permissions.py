"""
User Permission Management API Endpoints
Handles user-role assignments and custom scope management
"""

from typing import List
from fastapi import APIRouter, HTTPException, Security

from app.deps import SessionDep, get_current_user
from app.models import User, UserPublic, Message, RolePublic
from app.permissions import (
    get_user_effective_scopes,
    assign_role_to_user as assign_role_to_user_impl,
    remove_role_from_user as remove_role_from_user_impl,
    grant_custom_scope_to_user,
    revoke_custom_scope_from_user,
)
from app.db_crud import get_user_by_email
from pydantic import BaseModel


router = APIRouter(prefix="/user-permissions", tags=["user-permissions"])


# Pydantic models for API
class UserRoleAssignment(BaseModel):
    user_email: str
    role_name: str


class UserScopeGrant(BaseModel):
    user_email: str
    scope: str


class UserPermissionsResponse(BaseModel):
    user: UserPublic
    roles: List[RolePublic]
    custom_scopes: List[str]
    effective_scopes: List[str]


# User role assignment endpoints
@router.post("/assign-role", response_model=Message)
def assign_role_to_user(
    assignment: UserRoleAssignment,
    session: SessionDep,
    current_user: User = Security(get_current_user, scopes=["users:update"]),
):
    """Assign a role to a user"""
    user = get_user_by_email(session=session, email=assignment.user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    success = assign_role_to_user_impl(session, user, assignment.role_name)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")

    return Message(
        message=f"Role '{assignment.role_name}' assigned to user '{assignment.user_email}'"
    )


@router.post("/remove-role", response_model=Message)
def remove_role_from_user(
    assignment: UserRoleAssignment,
    session: SessionDep,
    current_user: User = Security(get_current_user, scopes=["users:update"]),
):
    """Remove a role from a user"""
    user = get_user_by_email(session=session, email=assignment.user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    success = remove_role_from_user_impl(session, user, assignment.role_name)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")

    return Message(
        message=f"Role '{assignment.role_name}' removed from user '{assignment.user_email}'"
    )


# Individual scope management endpoints
@router.post("/grant-scope", response_model=Message)
def grant_scope_to_user(
    grant: UserScopeGrant,
    session: SessionDep,
    current_user: User = Security(get_current_user, scopes=["users:update"]),
):
    """Grant an individual scope to a user"""
    user = get_user_by_email(session=session, email=grant.user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    success = grant_custom_scope_to_user(session, user, grant.scope)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid scope")

    return Message(
        message=f"Scope '{grant.scope}' granted to user '{grant.user_email}'"
    )


@router.post("/revoke-scope", response_model=Message)
def revoke_scope_from_user(
    grant: UserScopeGrant,
    session: SessionDep,
    current_user: User = Security(get_current_user, scopes=["users:update"]),
):
    """Revoke an individual scope from a user"""
    user = get_user_by_email(session=session, email=grant.user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    revoke_custom_scope_from_user(session, user, grant.scope)
    return Message(
        message=f"Scope '{grant.scope}' revoked from user '{grant.user_email}'"
    )


# User permissions view endpoints
@router.get("/{user_email}", response_model=UserPermissionsResponse)
def get_user_permissions(
    user_email: str,
    session: SessionDep,
    current_user: User = Security(get_current_user, scopes=["users:read"]),
):
    """Get a user's complete permission information"""
    user = get_user_by_email(session=session, email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    effective_scopes = list(get_user_effective_scopes(user))

    return UserPermissionsResponse(
        user=UserPublic.model_validate(user),
        roles=[
            RolePublic(
                id=role.id,
                name=role.name,
                description=role.description,
                scopes=role.scopes or [],
            )
            for role in user.roles
        ],
        custom_scopes=user.custom_scopes or [],
        effective_scopes=sorted(effective_scopes),
    )
