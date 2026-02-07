"""merge heads

Revision ID: 81bdaea227a7
Revises: 7f1c2b9a0d21, b05211d75551
Create Date: 2026-02-07 01:56:02.718907

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "81bdaea227a7"
down_revision: Union[str, None] = ("7f1c2b9a0d21", "b05211d75551")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
