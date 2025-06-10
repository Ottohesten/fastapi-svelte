"""
Role Management API Endpoints
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Security
from sqlmodel import select

from app.deps import SessionDep, get_current_user
from app.models import Role, User, Message
from app.permissions import AVAILABLE_SCOPES, ROLE_TEMPLATES, create_role_from_template
from pydantic import BaseModel


router = APIRouter(prefix="/roles", tags=["roles"])


# Pydantic models for API
class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scopes: List[str] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scopes: Optional[List[str]] = None


class RolePublic(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    scopes: List[str]


# Role CRUD endpoints
@router.get("/", response_model=List[RolePublic])
def list_roles(session: SessionDep, current_user: User = Security(get_current_user, scopes=["roles:read"])):
    """List all roles"""
    roles = session.exec(select(Role)).all()
    return [
        RolePublic(
            id=role.id,
            name=role.name,
            description=role.description,
            scopes=role.scopes or []
        )
        for role in roles
    ]


@router.post("/", response_model=RolePublic)
def create_role(role_data: RoleCreate,session: SessionDep,current_user: User = Security(get_current_user, scopes=["roles:create"])):
    """Create a new role"""
    # Validate scopes
    invalid_scopes = set(role_data.scopes) - AVAILABLE_SCOPES
    if invalid_scopes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scopes: {', '.join(invalid_scopes)}"
        )
    
    # Check if role name already exists
    existing_role = session.exec(
        select(Role).where(Role.name == role_data.name)
    ).first()
    if existing_role:
        raise HTTPException(
            status_code=400,
            detail=f"Role '{role_data.name}' already exists"
        )
    
    role = Role(
        name=role_data.name,
        description=role_data.description,
        scopes=role_data.scopes
    )
    session.add(role)
    session.commit()
    session.refresh(role)
    
    return RolePublic(
        id=role.id,
        name=role.name,
        description=role.description,
        scopes=role.scopes or []
    )


@router.get("/{role_id}", response_model=RolePublic)
def get_role(role_id: uuid.UUID, session: SessionDep, current_user: User = Security(get_current_user, scopes=["roles:read"])):
    """Get a specific role"""
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return RolePublic(
        id=role.id,
        name=role.name,
        description=role.description,
        scopes=role.scopes or []
    )


@router.put("/{role_id}", response_model=RolePublic)
def update_role(role_id: uuid.UUID, role_data: RoleUpdate, session: SessionDep, current_user: User = Security(get_current_user, scopes=["roles:update"])):
    """Update a role"""
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Validate scopes if provided
    if role_data.scopes is not None:
        invalid_scopes = set(role_data.scopes) - AVAILABLE_SCOPES
        if invalid_scopes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scopes: {', '.join(invalid_scopes)}"
            )
        role.scopes = role_data.scopes
    
    if role_data.name is not None:
        # Check if new name conflicts
        existing_role = session.exec(
            select(Role).where(Role.name == role_data.name, Role.id != role_id)
        ).first()
        if existing_role:
            raise HTTPException(
                status_code=400,
                detail=f"Role '{role_data.name}' already exists"
            )
        role.name = role_data.name
    
    if role_data.description is not None:
        role.description = role_data.description
    
    session.add(role)
    session.commit()
    session.refresh(role)
    
    return RolePublic(
        id=role.id,
        name=role.name,
        description=role.description,
        scopes=role.scopes or []
    )


@router.delete("/{role_id}", response_model=Message)
def delete_role(role_id: uuid.UUID, session: SessionDep, current_user: User = Security(get_current_user, scopes=["roles:delete"])):
    """Delete a role"""
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    session.delete(role)
    session.commit()
    
    return Message(message=f"Role '{role.name}' deleted successfully")


# Role template endpoints
@router.get("/templates/", response_model=dict)
def list_role_templates( current_user: User = Security(get_current_user, scopes=["roles:read"])):
    """List available role templates"""
    return {"templates": ROLE_TEMPLATES}


@router.post("/from-template/{template_key}", response_model=RolePublic)
def create_role_from_template_endpoint(template_key: str, session: SessionDep, current_user: User = Security(get_current_user, scopes=["roles:create"])):
    """Create a role from a predefined template"""
    try:
        role = create_role_from_template(session, template_key)
        return RolePublic(
            id=role.id,
            name=role.name,
            description=role.description,
            scopes=role.scopes or []
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Available scopes endpoint
@router.get("/scopes/available", response_model=dict)
def list_available_scopes(current_user: User = Security(get_current_user, scopes=["roles:read"])):
    """List all available scopes"""
    return {"scopes": sorted(list(AVAILABLE_SCOPES))}
