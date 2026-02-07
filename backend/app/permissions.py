"""
Permission and Role Management Utilities
"""

from sqlmodel import Session, select
from app.models import User, Role
from typing import Set, List


# Define all available scopes in your application
AVAILABLE_SCOPES = {
    # Core content permissions
    "recipes:read",
    "recipes:create",
    "recipes:update",
    "recipes:delete",
    "ingredients:read",
    "ingredients:create",
    "ingredients:update",
    "ingredients:delete",
    # Game permissions
    "games:read",
    "games:create",
    "games:update",
    "games:delete",
    # Game Player permissions
    "players:read",
    "players:create",
    "players:update",
    "players:delete",
    # Game Teams permissions
    "teams:read",
    "teams:create",
    "teams:update",
    "teams:delete",
    # Drinks Permissions
    "drinks:read",
    "drinks:create",
    "drinks:update",
    "drinks:delete",
    # User management permissions
    "users:read",
    "users:create",
    "users:update",
    "users:delete",
    # Role permissions
    "roles:read",
    "roles:create",
    "roles:update",
    "roles:delete",
    # Admin permissions
    # "admin:manage_users", "admin:manage_roles", "admin:manage_permissions",
    # "admin:system_settings", "admin:audit_logs",
    # Special permissions
    # "api:access", "analytics:read", "beta:features",
    # "recipes:feature", "ingredients:import", "games:broadcast"
}

# Predefined role templates
ROLE_TEMPLATES = {
    "viewer": {
        "name": "Viewer",
        "description": "Basic read-only access to recipes and ingredients",
        "scopes": ["recipes:read", "ingredients:read"],
    },
    "recipe_contributor": {
        "name": "Recipe Contributor",
        "description": "Can create and manage their own recipes",
        "scopes": [
            "recipes:read",
            "recipes:create",
            "recipes:update",
            "recipes:delete",
            "ingredients:read",
            "ingredients:create",
        ],
    },
    "recipe_moderator": {
        "name": "Recipe Moderator",
        "description": "Can moderate all recipe content",
        "scopes": [
            "recipes:read",
            "recipes:create",
            "recipes:update",
            "recipes:delete",
            "ingredients:read",
            "ingredients:create",
            "ingredients:update",
            "ingredients:delete",
        ],
    },
    "game_master": {
        "name": "Game Master",
        "description": "Can manage game sessions and players",
        "scopes": [
            "games:read",
            "games:create",
            "games:update",
            "games:delete",
        ],
    },
    "user_manager": {
        "name": "User Manager",
        "description": "Can manage user accounts but not system settings",
        "scopes": [
            "users:read",
            "users:update",
            "users:create",
            "users:delete",
        ],
    },
    "content_manager": {
        "name": "Content Manager",
        "description": "Can manage all content but not users",
        "scopes": [
            "recipes:read",
            "recipes:create",
            "recipes:update",
            "recipes:delete",
            "ingredients:read",
            "ingredients:create",
            "ingredients:update",
            "ingredients:delete",
            "games:read",
            "games:create",
            "games:update",
            "games:delete",
        ],
    },
    "administrator": {
        "name": "Administrator",
        "description": "Full access to user and system management",
        "scopes": [
            "users:read",
            "users:create",
            "users:update",
            "users:delete",
            "roles:read",
            "roles:create",
            "roles:update",
            "roles:delete",
            "recipes:read",
            "recipes:create",
            "recipes:update",
            "recipes:delete",
            "ingredients:read",
            "ingredients:create",
            "ingredients:update",
            "ingredients:delete",
            "games:read",
            "games:create",
            "games:update",
            "games:delete",
            "players:read",
            "players:create",
            "players:update",
            "players:delete",
            "teams:read",
            "teams:create",
            "teams:update",
            "teams:delete",
            "drinks:read",
            "drinks:create",
            "drinks:update",
            "drinks:delete",
        ],
    },
}


def get_user_effective_scopes(user: User) -> Set[str]:
    """
    Calculate user's effective permissions from roles + individual grants
    """
    if user.is_superuser:
        return AVAILABLE_SCOPES.copy()  # Superuser gets all permissions

    effective_scopes = set()

    # Add role-based scopes
    for role in user.roles:
        if role.scopes:
            effective_scopes.update(role.scopes)

    # Add individual custom scopes
    if user.custom_scopes:
        effective_scopes.update(user.custom_scopes)

    return effective_scopes


def user_has_scope(user: User, required_scope: str) -> bool:
    """
    Check if user has a specific scope
    """
    if user.is_superuser:
        return True

    effective_scopes = get_user_effective_scopes(user)
    return required_scope in effective_scopes


def user_has_any_scope(user: User, required_scopes: List[str]) -> bool:
    """
    Check if user has any of the required scopes
    """
    if user.is_superuser:
        return True

    effective_scopes = get_user_effective_scopes(user)
    return bool(effective_scopes.intersection(set(required_scopes)))


def user_has_all_scopes(user: User, required_scopes: List[str]) -> bool:
    """
    Check if user has all of the required scopes
    """
    if user.is_superuser:
        return True

    effective_scopes = get_user_effective_scopes(user)
    return set(required_scopes).issubset(effective_scopes)


def create_role_from_template(session: Session, template_key: str) -> Role:
    """
    Create a role from a predefined template
    """
    if template_key not in ROLE_TEMPLATES:
        raise ValueError(f"Unknown role template: {template_key}")

    template = ROLE_TEMPLATES[template_key]

    # Check if role already exists
    existing_role = session.exec(
        select(Role).where(Role.name == template["name"])
    ).first()

    if existing_role:
        # Update existing role with template scopes
        existing_role.description = (
            str(template["description"]) if template.get("description") else None
        )
        existing_role.scopes = (
            list(template["scopes"]) if isinstance(template.get("scopes"), list) else []
        )
        session.add(existing_role)
        session.commit()
        session.refresh(existing_role)
        return existing_role

    # Create new role
    role = Role(
        name=template["name"],
        description=template["description"],
        scopes=template["scopes"],
    )
    session.add(role)
    session.commit()
    session.refresh(role)
    return role


def initialize_default_roles(session: Session) -> List[Role]:
    """
    Initialize all default roles from templates
    """
    created_roles = []
    for template_key in ROLE_TEMPLATES.keys():
        role = create_role_from_template(session, template_key)
        created_roles.append(role)

    return created_roles


def assign_role_to_user(session: Session, user: User, role_name: str) -> bool:
    """
    Assign a role to a user
    """
    role = session.exec(select(Role).where(Role.name == role_name)).first()
    if not role:
        return False

    if role not in user.roles:
        user.roles.append(role)
        session.add(user)
        session.commit()
        session.refresh(user)

    return True


def remove_role_from_user(session: Session, user: User, role_name: str) -> bool:
    """
    Remove a role from a user
    """
    role = session.exec(select(Role).where(Role.name == role_name)).first()
    if not role:
        return False

    if role in user.roles:
        user.roles.remove(role)
        session.add(user)
        session.commit()
        session.refresh(user)

    return True


def grant_custom_scope_to_user(session: Session, user: User, scope: str) -> bool:
    """
    Grant an individual scope to a user
    """
    if scope not in AVAILABLE_SCOPES:
        return False

    if scope not in user.custom_scopes:
        user.custom_scopes.append(scope)
        session.add(user)
        session.commit()
        session.refresh(user)

    return True


def revoke_custom_scope_from_user(session: Session, user: User, scope: str) -> bool:
    """
    Revoke an individual scope from a user
    """
    if scope in user.custom_scopes:
        user.custom_scopes.remove(scope)
        session.add(user)
        session.commit()
        session.refresh(user)

    return True
