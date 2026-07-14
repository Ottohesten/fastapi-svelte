"""Add barcode to ingredient

Revision ID: e3b7a9c2d4f6
Revises: c5b4e7a9d2f1
Create Date: 2026-07-14 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3b7a9c2d4f6"
down_revision: Union[str, None] = "c5b4e7a9d2f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ingredient", sa.Column("barcode", sa.String(length=24), nullable=True)
    )
    op.create_index(
        op.f("ix_ingredient_barcode"), "ingredient", ["barcode"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ingredient_barcode"), table_name="ingredient")
    op.drop_column("ingredient", "barcode")
