import uuid
from pydantic import BaseModel, EmailStr, computed_field
from sqlmodel import Field, SQLModel, Relationship, Column, JSON
from sqlalchemy import DateTime
from typing import Optional
from datetime import datetime, timezone
# from permissions.roles import Role


class UserRoleLink(SQLModel, table=True):
    user_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    role_id: uuid.UUID | None = Field(
        default=None, foreign_key="role.id", primary_key=True
    )


class Role(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    description: str | None = None
    users: list["User"] = Relationship(back_populates="roles", link_model=UserRoleLink)
    scopes: list[str] = Field(
        default_factory=list,
        description="List of scopes that this role has access to",
        sa_column=Column(JSON, nullable=False, server_default="[]"),
    )


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
        default_factory=list,
        description="List of custom scopes that this user has access to",
        sa_column=Column(JSON),
    )

    # H.C game
    game_sessions: list["GameSession"] = Relationship(back_populates="owner")
    refresh_tokens: list["RefreshToken"] = Relationship(
        back_populates="user", cascade_delete=True
    )


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)
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


class UserMePublic(UserPublic):
    scopes: list[str]


class RolePublic(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    scopes: list[str]


class RoleCreate(BaseModel):
    name: str
    description: str | None = None
    scopes: list[str] = []


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    scopes: list[str] | None = None


class UserWithPermissionsPublic(UserPublic):
    roles: list[RolePublic]
    custom_scopes: list[str]
    effective_scopes: list[str]


class UsersWithPermissionsPublic(SQLModel):
    data: list[UserWithPermissionsPublic]
    count: int


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "Bearer"
    # Optional refresh token if we ever decide to return it in body (we'll use cookie primarily)
    refresh_token: str | None = None


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
    title: str | None = Field(default=None, min_length=1, max_length=255)


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
    recipe_id: uuid.UUID | None = Field(
        default=None, foreign_key="recipe.id", primary_key=True
    )
    ingredient_id: uuid.UUID | None = Field(
        default=None, foreign_key="ingredient.id", primary_key=True
    )

    # units enum
    amount: float = Field(
        default=1.0, ge=0, description="Amount of the ingredient in the recipe"
    )
    unit: str = Field(
        default="g",
        max_length=10,
        description="Unit of the amount, e.g. g, ml, pcs, etc.",
    )

    recipe: "Recipe" = Relationship(back_populates="ingredient_links")
    ingredient: "Ingredient" = Relationship(back_populates="recipe_links")


class RecipeIngredientLinkCreate(SQLModel):
    """
    Create a new recipe ingredient link.
    """

    ingredient_id: uuid.UUID
    amount: float = Field(
        default=1.0, ge=0, description="Amount of the ingredient in the recipe"
    )
    unit: str = Field(
        default="g",
        max_length=10,
        description="Unit of the amount, e.g. g, ml, pcs, etc.",
    )


class RecipeIngredientLinkPublic(SQLModel):
    """
    Public class for recipe ingredient link.
    """

    ingredient: "IngredientPublic"
    amount: float
    unit: str = Field(
        default="g",
        max_length=10,
        description="Unit of the amount, e.g. g, ml, pcs, etc.",
    )


class RecipeSubRecipeLinkCreate(SQLModel):
    sub_recipe_id: uuid.UUID
    scale_factor: float = Field(
        default=1.0,
        gt=0,
        description=(
            "Multiplier applied to the linked sub-recipe. "
            "Example: 0.25 means a quarter of the recipe."
        ),
    )


class RecipeSubRecipePublic(SQLModel):
    id: uuid.UUID
    title: str
    servings: int
    image: Optional[str] = None


class RecipeSubRecipeLinkPublic(SQLModel):
    sub_recipe: RecipeSubRecipePublic
    scale_factor: float

    @computed_field
    @property
    def scaled_servings(self) -> float:
        return round(self.sub_recipe.servings * self.scale_factor, 2)


#####################################################################################
# Recipes


class RecipeBase(SQLModel):
    title: str = Field(max_length=255, min_length=1)
    instructions: Optional[str] = Field(default=None, max_length=9999)
    servings: int = Field(default=1)
    image: Optional[str] = Field(default=None, max_length=1000)


class RecipeCreate(RecipeBase):
    ingredients: list[RecipeIngredientLinkCreate]
    sub_recipes: list[RecipeSubRecipeLinkCreate] = []


class RecipePublic(RecipeBase):
    id: uuid.UUID
    owner: UserPublic
    ingredient_links: list[RecipeIngredientLinkPublic]
    sub_recipe_links: list[RecipeSubRecipeLinkPublic] = []

    def _amount_to_grams(self, link: RecipeIngredientLinkPublic) -> float:
        """
        Convert a recipe ingredient amount to grams for nutrition/weight calculations.
        """
        amount_in_grams = link.amount
        if link.unit == "kg":
            amount_in_grams = link.amount * 1000
        elif link.unit == "L":
            amount_in_grams = link.amount * 1000
        elif link.unit == "pcs":
            amount_in_grams = link.amount * link.ingredient.weight_per_piece

        # For "g" and "ml" we keep a 1:1 conversion for now.
        return amount_in_grams

    def _sum_nutrient(self, nutrient_field: str) -> float:
        """
        Sum nutrient values for all linked ingredients.
        Nutrients are stored as value per 100g on Ingredient.
        """
        total = 0.0
        for link in self.ingredient_links:
            amount_in_grams = self._amount_to_grams(link)
            nutrient_per_100g = getattr(link.ingredient, nutrient_field, 0)
            total += (nutrient_per_100g * amount_in_grams) / 100
        return total

    def _per_serving(self, total_value: float) -> float:
        if self.servings <= 0:
            return 0.0
        return total_value / self.servings

    @computed_field
    @property
    def total_calories(self) -> int:
        """Calculate total calories for the entire recipe based on ingredients and their amounts."""
        return round(self._sum_nutrient("calories"))

    @computed_field
    @property
    def calories_per_serving(self) -> int:
        """Calculate calories per serving."""
        return round(self._per_serving(self.total_calories))

    @computed_field
    @property
    def total_carbohydrates(self) -> float:
        """Calculate total carbohydrates for the entire recipe in grams."""
        return round(self._sum_nutrient("carbohydrates"), 1)

    @computed_field
    @property
    def total_fat(self) -> float:
        """Calculate total fat for the entire recipe in grams."""
        return round(self._sum_nutrient("fat"), 1)

    @computed_field
    @property
    def total_protein(self) -> float:
        """Calculate total protein for the entire recipe in grams."""
        return round(self._sum_nutrient("protein"), 1)

    @computed_field
    @property
    def carbohydrates_per_serving(self) -> float:
        """Calculate carbohydrates per serving in grams."""
        return round(self._per_serving(self.total_carbohydrates), 1)

    @computed_field
    @property
    def fat_per_serving(self) -> float:
        """Calculate fat per serving in grams."""
        return round(self._per_serving(self.total_fat), 1)

    @computed_field
    @property
    def protein_per_serving(self) -> float:
        """Calculate protein per serving in grams."""
        return round(self._per_serving(self.total_protein), 1)

    @computed_field
    @property
    def calculated_weight(self) -> int:
        """The calculated weight of the recipe based on the ingredients and their amounts. Returns the total weight in grams."""
        total_weight = sum(
            self._amount_to_grams(link) for link in self.ingredient_links
        )
        return round(total_weight)

    @computed_field
    @property
    def calories_per_100g(self) -> int:
        """Calculate calories per 100g of the recipe."""
        total_weight = self.calculated_weight
        if total_weight <= 0:
            return 0
        return round((self.total_calories / total_weight) * 100)


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

    ingredient_links: list[RecipeIngredientLink] = Relationship(
        back_populates="recipe", cascade_delete=True
    )
    sub_recipe_links: list["RecipeSubRecipeLink"] = Relationship(
        back_populates="parent_recipe",
        sa_relationship_kwargs={"foreign_keys": "RecipeSubRecipeLink.parent_recipe_id"},
        cascade_delete=True,
    )
    parent_recipe_links: list["RecipeSubRecipeLink"] = Relationship(
        back_populates="sub_recipe",
        sa_relationship_kwargs={"foreign_keys": "RecipeSubRecipeLink.sub_recipe_id"},
        cascade_delete=True,
    )

    # class Config:
    #     arbitrary_types_allowed = True


#####################################################################################
# Recipe Sub-Recipe links


class RecipeSubRecipeLink(SQLModel, table=True):
    parent_recipe_id: uuid.UUID | None = Field(
        default=None, foreign_key="recipe.id", primary_key=True
    )
    sub_recipe_id: uuid.UUID | None = Field(
        default=None, foreign_key="recipe.id", primary_key=True
    )
    scale_factor: float = Field(
        default=1.0,
        gt=0,
        description=(
            "Multiplier applied to the linked sub-recipe. "
            "Example: 0.25 means a quarter of the recipe."
        ),
    )

    parent_recipe: "Recipe" = Relationship(
        back_populates="sub_recipe_links",
        sa_relationship_kwargs={"foreign_keys": "RecipeSubRecipeLink.parent_recipe_id"},
    )
    sub_recipe: "Recipe" = Relationship(
        back_populates="parent_recipe_links",
        sa_relationship_kwargs={"foreign_keys": "RecipeSubRecipeLink.sub_recipe_id"},
    )


#####################################################################################
# Ingredients


class IngredientBase(SQLModel):
    title: str = Field(max_length=255, min_length=1)
    calories: int = Field(
        default=0, ge=0, description="Calories per 100g of the ingredient"
    )
    carbohydrates: float = Field(
        default=0,
        ge=0,
        description="Carbohydrates per 100g of the ingredient in grams",
    )
    fat: float = Field(
        default=0,
        ge=0,
        description="Fat per 100g of the ingredient in grams",
    )
    protein: float = Field(
        default=0,
        ge=0,
        description="Protein per 100g of the ingredient in grams",
    )
    weight_per_piece: int = Field(
        default=100,
        ge=0,
        description="Average weight per piece in grams (used when unit is 'pcs')",
    )
    # pass


class IngredientCreate(IngredientBase):
    pass


class IngredientPublic(IngredientBase):
    id: uuid.UUID
    # Make fields required for public responses so OpenAPI marks them as required
    title: str
    calories: int
    carbohydrates: float
    fat: float
    protein: float
    weight_per_piece: int
    # recipes: list[RecipePublic]


class Ingredient(IngredientBase, table=True):
    """
    Ingredient model

    Should have a title (will later be the primary key) and a list of recipes that use this ingredient. Amount and unit of the amount will be handled in the RecipeIngredientLink model
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255, min_length=1)
    calories: int = Field(
        default=0, ge=0, description="Calories per 100g of the ingredient"
    )
    carbohydrates: float = Field(
        default=0,
        ge=0,
        description="Carbohydrates per 100g of the ingredient in grams",
        sa_column_kwargs={"server_default": "0"},
    )
    fat: float = Field(
        default=0,
        ge=0,
        description="Fat per 100g of the ingredient in grams",
        sa_column_kwargs={"server_default": "0"},
    )
    protein: float = Field(
        default=0,
        ge=0,
        description="Protein per 100g of the ingredient in grams",
        sa_column_kwargs={"server_default": "0"},
    )
    weight_per_piece: int = Field(
        default=1,
        ge=0,
        description="Average weight per piece in grams (used when unit is 'pcs')",
        sa_column_kwargs={"server_default": "1"},
    )

    # recipes: list["Recipe"] = Relationship(back_populates="ingredients", link_model=RecipeIngredientLink)
    recipe_links: list["RecipeIngredientLink"] = Relationship(
        back_populates="ingredient", cascade_delete=True
    )


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
    created_at: datetime
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
    created_at: datetime = Field(
        default=datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    teams: Optional[list["GameTeam"]] = Relationship(
        back_populates="game_session", cascade_delete=True
    )
    players: Optional[list["GamePlayer"]] = Relationship(
        back_populates="game_session", cascade_delete=True
    )


class GamePlayerDrinkLink(SQLModel, table=True):
    """
    Link model for the many to many relationship between GamePlayer and Drink, with amount field
    """

    game_player_id: uuid.UUID | None = Field(
        default=None, foreign_key="gameplayer.id", primary_key=True
    )
    drink_id: uuid.UUID | None = Field(
        default=None, foreign_key="drink.id", primary_key=True
    )
    amount: int = Field(
        default=1, ge=1, description="How many of this drink the player has consumed"
    )

    game_player: "GamePlayer" = Relationship(back_populates="drink_links")
    drink: "Drink" = Relationship(back_populates="player_links")


class GamePlayerDrinkLinkCreate(SQLModel):
    """
    Create class for GamePlayerDrinkLink
    """

    drink_id: uuid.UUID
    amount: int = Field(
        default=1, ge=0, description="How many of this drink the player has consumed"
    )


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

    team_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="gameteam.id", nullable=True
    )
    team: Optional["GameTeam"] = Relationship(
        back_populates="players"
    )  # drinks: list["Drink"] = Relationship(back_populates="players", link_model=GamePlayerDrinkLink)
    drink_links: list["GamePlayerDrinkLink"] = Relationship(
        back_populates="game_player", cascade_delete=True
    )


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

    game_session_id: uuid.UUID = Field(
        default=None, foreign_key="gamesession.id", nullable=False
    )
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


class RefreshRequest(BaseModel):
    refresh_token: str


# Refresh token persistence for revocation/rotation
class RefreshToken(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    token_hash: str = Field(
        index=True, max_length=128, description="SHA256 of the refresh token"
    )
    jti: uuid.UUID = Field(default_factory=uuid.uuid4, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    revoked_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    user: Optional["User"] = Relationship(
        back_populates="refresh_tokens", sa_relationship_kwargs={"lazy": "selectin"}
    )


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
