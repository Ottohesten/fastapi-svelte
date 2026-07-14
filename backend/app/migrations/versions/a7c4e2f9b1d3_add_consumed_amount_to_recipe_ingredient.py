"""Add consumed amount to recipe ingredient links

Revision ID: a7c4e2f9b1d3
Revises: e3b7a9c2d4f6
Create Date: 2026-07-14 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7c4e2f9b1d3"
down_revision: Union[str, None] = "e3b7a9c2d4f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "recipeingredientlink",
        sa.Column("consumed_amount", sa.Float(), nullable=True),
    )
    op.create_check_constraint(
        "ck_recipeingredientlink_consumed_amount_lte_amount",
        "recipeingredientlink",
        "consumed_amount IS NULL OR "
        "(consumed_amount >= 0 AND consumed_amount <= amount)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_recipeingredientlink_consumed_amount_lte_amount",
        "recipeingredientlink",
        type_="check",
    )
    op.drop_column("recipeingredientlink", "consumed_amount")
