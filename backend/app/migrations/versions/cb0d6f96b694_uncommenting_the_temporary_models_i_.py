"""uncommenting the temporary models i created

Revision ID: cb0d6f96b694
Revises: 434c54812521
Create Date: 2025-01-24 03:42:12.846636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'cb0d6f96b694'
down_revision: Union[str, None] = '434c54812521'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('teampersonlink')
    op.drop_table('person')
    op.drop_table('team')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('teampersonlink',
    sa.Column('team_name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('person_name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['person_name'], ['person.name'], name='teampersonlink_person_name_fkey'),
    sa.ForeignKeyConstraint(['team_name'], ['team.name'], name='teampersonlink_team_name_fkey'),
    sa.PrimaryKeyConstraint('team_name', 'person_name', name='teampersonlink_pkey')
    )
    op.create_table('team',
    sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('location', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('name', name='team_pkey')
    )
    op.create_table('person',
    sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('age', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('height', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('name', name='person_pkey')
    )
    # ### end Alembic commands ###
