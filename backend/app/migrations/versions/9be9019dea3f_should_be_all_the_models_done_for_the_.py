"""should be all the models done for the game, but i might have fucked something up

Revision ID: 9be9019dea3f
Revises: e475e4b026d3
Create Date: 2025-05-04 04:13:41.339909

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9be9019dea3f'
down_revision: Union[str, None] = 'e475e4b026d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('gamesession')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('gamesession',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('owner_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('player_information', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('title', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], name='gamesession_owner_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='gamesession_pkey')
    )
    # ### end Alembic commands ###
