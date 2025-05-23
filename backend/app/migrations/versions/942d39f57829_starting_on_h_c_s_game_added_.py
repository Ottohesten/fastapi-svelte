"""Starting on H.C's game. Added GameSession model and relationship in user model and fixed typo in recipe model

Revision ID: 942d39f57829
Revises: aabd10773219
Create Date: 2025-04-29 03:24:10.174029

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '942d39f57829'
down_revision: Union[str, None] = 'aabd10773219'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('gamesession',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.Column('player_information', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_column('recipe', 'instrutions')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('recipe', sa.Column('instrutions', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.drop_table('gamesession')
    # ### end Alembic commands ###
