import uuid
from pydantic import BaseModel, EmailStr, computed_field
from sqlmodel import Field, SQLModel, Relationship, Column, JSON
from typing import Optional
# from permissions.roles import Role


class UserRoleLink(SQLModel, table=True):
    user_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", primary_key=True)
    role_id: uuid.UUID | None = Field(default=None, foreign_key="role.id", primary_key=True)



class Role(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    description: str | None = None
    users: list["User"] = Relationship(back_populates="roles", link_model=UserRoleLink)
    scopes: list[str] = Field(default_factory=list, description="List of scopes that this role has access to", sa_column=Column(JSON))



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
    custom_scopes: list[str] = Field(
        default_factory=list, description="List of custom scopes that this user has access to", sa_column=Column(JSON))

    # H.C game
    game_sessions: list["GameSession"] = Relationship(back_populates="owner")


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
    full_name: Optional[str] = Field(default=None, max_length=255)


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

    # units enum
    amount: float = Field(default=1.0, ge=0, description="Amount of the ingredient in the recipe")
    unit: str = Field(default="g", max_length=10, description="Unit of the amount, e.g. g, ml, pcs, etc.")

    recipe: "Recipe" = Relationship(back_populates="ingredient_links")
    ingredient: "Ingredient" = Relationship(back_populates="recipe_links")




class RecipeIngredientLinkCreate(SQLModel):
    """
    Create a new recipe ingredient link.
    """
    ingredient_id: uuid.UUID
    amount: float = Field(default=1.0, ge=0, description="Amount of the ingredient in the recipe")
    unit: str = Field(default="g", max_length=10, description="Unit of the amount, e.g. g, ml, pcs, etc.")


class RecipeIngredientLinkPublic(SQLModel):
    """
    Public class for recipe ingredient link.
    """
    ingredient: "IngredientPublic"
    amount: float
    unit: str = Field(default="g", max_length=10, description="Unit of the amount, e.g. g, ml, pcs, etc.")

#####################################################################################
# Recipes

class RecipeBase(SQLModel):
    title: str = Field(max_length=255, min_length=1)
    instructions: Optional[str]  = Field(default=None, max_length=9999)
    servings: int = Field(default=1)


class RecipeCreate(RecipeBase):
    ingredients: list[RecipeIngredientLinkCreate] 


class RecipePublic(RecipeBase):
    id: uuid.UUID 
    owner: UserPublic
    ingredient_links: list[RecipeIngredientLinkPublic]
    
    @computed_field
    @property
    def total_calories(self) -> int:
        """Calculate total calories for the entire recipe based on ingredients and their amounts."""
        total = 0
        for link in self.ingredient_links:
            # Convert amount to standardized unit (grams) for calculation
            amount_in_grams = link.amount
            if link.unit == "kg":
                amount_in_grams = link.amount * 1000
            elif link.unit == "ml":
                # Assume 1ml = 1g for simplicity (works for most liquids)
                amount_in_grams = link.amount
            elif link.unit == "L":
                amount_in_grams = link.amount * 1000
            elif link.unit == "pcs":
                # For pieces, assume average weight of 50g per piece
                # This could be made more sophisticated with ingredient-specific weights
                amount_in_grams = link.amount * 50
            
            # Calculate calories: (calories_per_100g * amount_in_grams) / 100
            ingredient_calories = (link.ingredient.calories * amount_in_grams) / 100
            total += ingredient_calories
            
        return round(total)
    
    @computed_field
    @property
    def calories_per_serving(self) -> int:
        """Calculate calories per serving."""
        if self.servings <= 0:
            return 0
        return round(self.total_calories / self.servings)
    

    @computed_field
    @property
    def calculated_weight(self) -> int:
        """The calculated weight of the recipe based on the ingredients and their amounts. Returns the total weight in grams."""
        total_weight = 0
        for link in self.ingredient_links:
            # Convert amount to standardized unit (grams) for calculation
            amount_in_grams = link.amount
            if link.unit == "kg":
                amount_in_grams = link.amount * 1000
            elif link.unit == "ml":
                # Assume 1ml = 1g for simplicity (works for most liquids)
                amount_in_grams = link.amount
            elif link.unit == "L":
                amount_in_grams = link.amount * 1000
            elif link.unit == "pcs":
                # For pieces, assume average weight of 50g per piece
                # This could be made more sophisticated with ingredient-specific weights
                amount_in_grams = link.amount * 50

            total_weight += amount_in_grams

        return round(total_weight)


class Recipe(RecipeBase, table=True):
    """
    Recipe model

    Should have an owner and a list of ingredients. However a recipe for every ingredints, the ingredient should also have an amount of that ingredient and the unit of the amount
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    instructions: Optional[str] = Field(default=None, max_length=9999)

    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    owner: User = Relationship(back_populates="recipes")

    # we will use this field to be able to scale the recipe, can not be less than 1
    servings: int = Field(default=1)

    # image
    # image: str | None = Field(default=None, max_length=255)

    ingredient_links: list[RecipeIngredientLink] = Relationship(back_populates="recipe", cascade_delete=True)
    


    # class Config:
    #     arbitrary_types_allowed = True




#####################################################################################
# Ingredients

class IngredientBase(SQLModel):
    title: str = Field(max_length=255, min_length=1)
    calories: int = Field(default=0, ge=0, description="Calories per 100g of the ingredient")
    # pass

class IngredientCreate(IngredientBase):
    pass

class IngredientPublic(IngredientBase):
    id: uuid.UUID
    # recipes: list[RecipePublic]


class Ingredient(IngredientBase, table=True):
    """
    Ingredient model

    Should have a title (will later be the primary key) and a list of recipes that use this ingredient. Amount and unit of the amount will be handled in the RecipeIngredientLink model
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255, min_length=1)
    calories: int = Field(default=0, ge=0, description="Calories per 100g of the ingredient")

    # recipes: list["Recipe"] = Relationship(back_populates="ingredients", link_model=RecipeIngredientLink)
    recipe_links: list["RecipeIngredientLink"] = Relationship(back_populates="ingredient", cascade_delete=True)

    


# for H.C game

"""
The game has a session. Each session has a title, a list of players and these players can be part of a team or not. Each team can have multiple players, but each player can only be in one team.

"""

class GameSessionBase(SQLModel):
    """
    Base class for game session. Should have a title and a list of players and their information (scores etc.)
    """
    title: str = Field(max_length=255, min_length=1)


class GameSessionCreate(GameSessionBase):
    teams: Optional[list["GameTeamCreate"]] = None


class GameSessionPublic(GameSessionBase):
    """
    Game session model

    Should have an owner (user) and a list of players and their information (scores etc.)
    """
    id: uuid.UUID
    owner: UserPublic
    players: list["GamePlayerPublic"]
    teams: list["GameTeamPublic"]

class GameSessionUpdate(GameSessionBase):
    """
    Game session model

    Should have an owner (user) and a list of players and their information (scores etc.)
    """
    id: uuid.UUID | None = None
    players: list["GamePlayer"] | None = None
    teams: list["GameTeam"] | None = None


class GameSession(GameSessionBase, table=True):
    """
    A game session that has an id, a user that created it (admin) and a list of players and their information (scores etc.)
    """
    title: str = Field(max_length=255, min_length=1, nullable=True)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    owner: User = Relationship(back_populates="game_sessions")

    teams: Optional[list["GameTeam"]] = Relationship(back_populates="game_session", cascade_delete=True)
    players: Optional[list["GamePlayer"]] = Relationship(back_populates="game_session", cascade_delete=True)




class GamePlayerDrinkLink(SQLModel, table=True):
    """
    Link model for the many to many relationship between GamePlayer and Drink, with amount field
    """
    game_player_id: uuid.UUID | None = Field(default=None, foreign_key="gameplayer.id", primary_key=True)
    drink_id: uuid.UUID | None = Field(default=None, foreign_key="drink.id", primary_key=True)
    amount: int = Field(default=1, ge=1, description="How many of this drink the player has consumed")

    game_player: "GamePlayer" = Relationship(back_populates="drink_links")
    drink: "Drink" = Relationship(back_populates="player_links")


class GamePlayerDrinkLinkCreate(SQLModel):
    """
    Create class for GamePlayerDrinkLink
    """
    drink_id: uuid.UUID
    amount: int = Field(default=1, ge=0, description="How many of this drink the player has consumed")

class GamePlayerDrinkLinkPublic(SQLModel):
    """
    Public class for GamePlayerDrinkLink
    """
    amount: int
    drink: "DrinkPublic"


class GamePlayerBase(SQLModel):
    """
    Base class for game player
    """
    name: str = Field(max_length=255, min_length=1)


class GamePlayerCreate(GamePlayerBase):
    """
    Create class for game player
    """
    team_id: Optional[uuid.UUID] = None

class GamePlayerUpdate(GamePlayerBase):
    """
    Update class for game player, can update name and team, can not change game session
    """
    name: Optional[str] = None
    team_id: Optional[uuid.UUID] = None
    drinks: Optional[list[GamePlayerDrinkLinkCreate]] = None

    # be able to add drinks to the player


class GamePlayerPublic(GamePlayerBase):
    """
    Public class for game player
    """
    id: uuid.UUID
    # game_session: GameSessionPublic
    game_session_id: uuid.UUID
    team_id: Optional[uuid.UUID] = None
    team: Optional["GameTeamPlayerPublic"] = None
    drink_links: list["GamePlayerDrinkLinkPublic"]

class GamePlayer(GamePlayerBase, table=True):
    """
    Game player model

    Should have a name, a team and a list of drinks (many to many relationship)
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, min_length=1)

    game_session_id: uuid.UUID = Field(foreign_key="gamesession.id", nullable=False)
    game_session: GameSession = Relationship(back_populates="players")

    team_id: Optional[uuid.UUID] = Field(default=None, foreign_key="gameteam.id", nullable=True)
    team: Optional["GameTeam"] = Relationship(back_populates="players")    # drinks: list["Drink"] = Relationship(back_populates="players", link_model=GamePlayerDrinkLink)
    drink_links: list["GamePlayerDrinkLink"] = Relationship(back_populates="game_player", cascade_delete=True)



class GameTeamBase(SQLModel):
    """
    Base class for game team
    """
    name: str = Field(max_length=255, min_length=1)
    


class GameTeamCreate(GameTeamBase):
    pass



class GameTeamPublic(GameTeamBase):
    """
    Public class for game team
    """
    id: uuid.UUID
    players: list["GamePlayer"]
    game_session_id: uuid.UUID
    # game_session: GameSessionPublic


class GameTeamPlayerPublic(GameTeamBase):
    name: str


class GameTeam(GameTeamBase, table=True):
    """
    Game team model

    Should have a name and a list of players. Each player can only be in one team.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, min_length=1)
    players: Optional[list["GamePlayer"]] = Relationship(back_populates="team")

    game_session_id: uuid.UUID = Field(default=None, foreign_key="gamesession.id", nullable=False)
    game_session: "GameSession" = Relationship(back_populates="teams")



class DrinkBase(SQLModel):
    name: str = Field(max_length=255, min_length=1)

class DrinkCreate(DrinkBase):
    pass


class DrinkPublic(DrinkBase):
    name: str
    id: uuid.UUID

class Drink(DrinkBase, table=True):
    """
    Drink model

    Parameters:
    - name: str
    - players: list[GamePlayer] | None
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, min_length=1)


    # players: list["GamePlayer"] | None = Relationship(back_populates="drinks", link_model=GamePlayerDrinkLink)
    player_links: list["GamePlayerDrinkLink"] = Relationship(back_populates="drink")
















#####################################################################################
# 


# Generic message
class Message(BaseModel):
    message: str

# HTTPException detail
class HTTPExceptionDetail(BaseModel):
    detail: str




# Team and Person models
# class TeamPersonLink(SQLModel, table=True):
#     team_name: str = Field(foreign_key="team.name", primary_key=True)
#     person_name: str = Field(foreign_key="person.name", primary_key=True)


# class Person(SQLModel, table=True):
#     name: str = Field(max_length=255, min_length=1, primary_key=True)
#     age: int
#     height: int # cm

#     team: "Team" = Relationship(back_populates="people", link_model=TeamPersonLink)


# class Team(SQLModel, table=True):
#     name: str = Field(max_length=255, min_length=1, primary_key=True)
#     location: str

#     people: List["Person"] = Relationship(back_populates="team", link_model=TeamPersonLink)