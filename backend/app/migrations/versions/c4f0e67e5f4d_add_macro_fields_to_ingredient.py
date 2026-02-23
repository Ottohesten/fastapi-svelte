"""add_macro_fields_to_ingredient

Revision ID: c4f0e67e5f4d
Revises: 6d6808607378
Create Date: 2026-02-23 21:55:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4f0e67e5f4d"
down_revision: Union[str, None] = "6d6808607378"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ingredient",
        sa.Column("carbohydrates", sa.Float(), server_default="0", nullable=False),
    )
    op.add_column(
        "ingredient",
        sa.Column("fat", sa.Float(), server_default="0", nullable=False),
    )
    op.add_column(
        "ingredient",
        sa.Column("protein", sa.Float(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("ingredient", "protein")
    op.drop_column("ingredient", "fat")
    op.drop_column("ingredient", "carbohydrates")
