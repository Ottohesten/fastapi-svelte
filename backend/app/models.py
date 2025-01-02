import uuid
from pydantic import BaseModel, EmailStr
from sqlmodel import Field, SQLModel, Relationship
from typing import List
# from permissions.roles import Role



class HeroBase(SQLModel):
    name: str = Field(index=True)
    secret_name: str
    age: int | None = Field(default=None, index=True)


class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

class HeroCreate(HeroBase):
    pass

class HeroPublic(HeroBase):
    id: int

class HeroUpdate(SQLModel):
    name: str | None = None
    secret_name: str | None = None
    age: int | None = None


class UserRoleLink(SQLModel, table=True):
    user_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", primary_key=True)
    role_id: uuid.UUID | None = Field(default=None, foreign_key="role.id", primary_key=True)



class Role(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    description: str | None = None
    users: List["User"] = Relationship(back_populates="roles", link_model=UserRoleLink)



# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)

class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    roles: list["Role"] = Relationship(back_populates="users", link_model=UserRoleLink)
    recipes: list["Recipe"] = Relationship(back_populates="owner")


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)




# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "Bearer"


# Contents of JWT token
class TokenData(SQLModel):
    email: str | None = None
    scopes: list[str] = []


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)




# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int



#####################################################################################
# link model

class RecipeIngredientLink(SQLModel, table=True):
    recipe_id: uuid.UUID | None = Field(default=None, foreign_key="recipe.id", primary_key=True)
    ingredient_id: uuid.UUID | None = Field(default=None, foreign_key="ingredient.id", primary_key=True)
    amount: float
    unit: str



#####################################################################################
# Recipes

class RecipeBase(SQLModel):
    title: str = Field(max_length=255, min_length=1)
    description: str | None = Field(default=None, max_length=255)


class RecipeCreate(RecipeBase):
    ingredients: list["Ingredient"] = []



class Recipe(RecipeBase, table=True):
    """
    Recipe model

    Should have an owner and a list of ingredients. However a recipe for every ingredints, the ingredient should also have an amount of that ingredient and the unit of the amount
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=255)

    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    owner: User = Relationship(back_populates="recipes")

    ingredients: List["Ingredient"] = Relationship(back_populates="recipes", link_model=RecipeIngredientLink)


#####################################################################################
# Ingredients

class IngredientBase(SQLModel):
    pass


class Ingredient(IngredientBase, table=True):
    """
    Ingredient model

    Should have a name, a unit and a list of recipes that use that ingredient. The recipe should also have an amount of that ingredient and the unit of the amount
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    recipes: List["Recipe"] = Relationship(back_populates="ingredients", link_model=RecipeIngredientLink)














#####################################################################################
# 


# Generic message
class Message(SQLModel):
    message: str

# HTTPException detail
class HTTPExceptionDetail(BaseModel):
    detail: str