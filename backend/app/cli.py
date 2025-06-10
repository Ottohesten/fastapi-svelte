import typer
from sqlmodel import Session
from app.db import engine
from app.permissions import (
    initialize_default_roles, 
    ROLE_TEMPLATES, 
    AVAILABLE_SCOPES,
    assign_role_to_user,
    get_user_effective_scopes
)
from app.db_crud import get_user_by_email
from app.models import Role, User
from sqlmodel import select

app = typer.Typer()


@app.command()
def hello(name: str):
    print(f"Hello {name}")


@app.command()
def goodbye(name: str, formal: bool = False):
    if formal:
        print(f"Goodbye Ms. {name}. Have a good day.")
    else:
        print(f"Bye {name}!")


@app.command()
def init_roles():
    """Initialize default roles in the database"""
    with Session(engine) as session:
        roles = initialize_default_roles(session)
        print(f"✅ Created/Updated {len(roles)} default roles:")
        for role in roles:
            print(f"  - {role.name}: {len(role.scopes)} scopes")


@app.command()
def list_roles():
    """List all roles and their scopes"""
    with Session(engine) as session:
        roles = session.exec(select(Role)).all()
        
        if not roles:
            print("No roles found. Run 'init-roles' first.")
            return
        
        for role in roles:
            print(f"\n🎭 {role.name}")
            print(f"   Description: {role.description}")
            print(f"   Scopes: {', '.join(role.scopes) if role.scopes else 'None'}")


@app.command()
def list_scopes():
    """List all available scopes"""
    print("📋 Available Scopes:")
    for scope in sorted(AVAILABLE_SCOPES):
        print(f"  - {scope}")


@app.command()
def delete_role(role_name: str):
    """Delete a role by name"""
    with Session(engine) as session:
        role = session.exec(select(Role).where(Role.name == role_name)).first()
        if not role:
            print(f"❌ Role '{role_name}' not found")
            return
        
        session.delete(role)
        session.commit()
        print(f"✅ Deleted role '{role_name}'")

@app.command()
def delete_all_roles():
    """Delete all roles"""
    with Session(engine) as session:
        roles = session.exec(select(Role)).all()
        if not roles:
            print("No roles to delete.")
            return
        
        for role in roles:
            session.delete(role)
        
        session.commit()
        print(f"✅ Deleted {len(roles)} roles")


@app.command()
def assign_role(email: str, role_name: str):
    """Assign a role to a user by email"""
    with Session(engine) as session:
        user = get_user_by_email(session=session, email=email)
        if not user:
            print(f"❌ User with email '{email}' not found")
            return
        
        success = assign_role_to_user(session, user, role_name)
        if success:
            print(f"✅ Assigned role '{role_name}' to user '{email}'")
        else:
            print(f"❌ Role '{role_name}' not found")


@app.command()
def show_user_permissions(email: str):
    """Show a user's effective permissions"""
    with Session(engine) as session:
        user = get_user_by_email(session=session, email=email)
        if not user:
            print(f"❌ User with email '{email}' not found")
            return
        
        print(f"\n👤 User: {user.email}")
        print(f"   Superuser: {user.is_superuser}")
        print(f"   Active: {user.is_active}")
        
        print(f"\n🎭 Roles ({len(user.roles)}):")
        for role in user.roles:
            print(f"  - {role.name}")
        
        print(f"\n🔑 Custom Scopes ({len(user.custom_scopes)}):")
        for scope in user.custom_scopes:
            print(f"  - {scope}")
        
        effective_scopes = get_user_effective_scopes(user)
        print(f"\n✅ Effective Permissions ({len(effective_scopes)}):")
        for scope in sorted(effective_scopes):
            print(f"  - {scope}")


if __name__ == "__main__":
    app()