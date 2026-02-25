"""Reconcile removed meals schema

Revision ID: a1d4c07df17e
Revises: f9c2f8d6c1a1
Create Date: 2026-02-24 23:58:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1d4c07df17e"
down_revision: Union[str, None] = "f9c2f8d6c1a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_tables() -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return set(inspector.get_table_names())


def upgrade() -> None:
    tables = _get_tables()

    if "mealrecipelink" in tables:
        op.drop_table("mealrecipelink")
        tables.remove("mealrecipelink")

    if "meal" in tables:
        op.drop_table("meal")
        tables.remove("meal")

    if "recipesubrecipelink" not in tables:
        op.create_table(
            "recipesubrecipelink",
            sa.Column("parent_recipe_id", sa.Uuid(), nullable=False),
            sa.Column("sub_recipe_id", sa.Uuid(), nullable=False),
            sa.Column("scale_factor", sa.Float(), nullable=False, server_default="1.0"),
            sa.ForeignKeyConstraint(
                ["parent_recipe_id"],
                ["recipe.id"],
            ),
            sa.ForeignKeyConstraint(
                ["sub_recipe_id"],
                ["recipe.id"],
            ),
            sa.PrimaryKeyConstraint("parent_recipe_id", "sub_recipe_id"),
        )


def downgrade() -> None:
    tables = _get_tables()

    if "recipesubrecipelink" in tables:
        op.drop_table("recipesubrecipelink")
        tables.remove("recipesubrecipelink")

    if "meal" not in tables:
        op.create_table(
            "meal",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=9999), nullable=True),
            sa.Column("servings", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("owner_id", sa.Uuid(), nullable=False),
            sa.ForeignKeyConstraint(
                ["owner_id"],
                ["user.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        tables.add("meal")

    if "mealrecipelink" not in tables:
        op.create_table(
            "mealrecipelink",
            sa.Column("meal_id", sa.Uuid(), nullable=False),
            sa.Column("recipe_id", sa.Uuid(), nullable=False),
            sa.Column("scale_factor", sa.Float(), nullable=False, server_default="1.0"),
            sa.ForeignKeyConstraint(
                ["meal_id"],
                ["meal.id"],
            ),
            sa.ForeignKeyConstraint(
                ["recipe_id"],
                ["recipe.id"],
            ),
            sa.PrimaryKeyConstraint("meal_id", "recipe_id"),
        )
