"""Add recipe sub-recipe links

Revision ID: f9c2f8d6c1a1
Revises: c4f0e67e5f4d
Create Date: 2026-02-24 23:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f9c2f8d6c1a1"
down_revision: Union[str, None] = "c4f0e67e5f4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    op.drop_table("recipesubrecipelink")
