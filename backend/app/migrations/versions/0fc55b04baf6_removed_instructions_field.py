"""removed instructions field

Revision ID: 0fc55b04baf6
Revises: ce144e53b375
Create Date: 2025-02-19 15:19:40.279965

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '0fc55b04baf6'
down_revision: Union[str, None] = 'ce144e53b375'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('recipe', 'instructions')
    op.drop_column('recipe', 'instrutions')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('recipe', sa.Column('instrutions', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column('recipe', sa.Column('instructions', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
