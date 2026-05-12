"""merge multiple heads

Revision ID: a1fff358fd7e
Revises: b8c4a9f2d3e1, ce5737ef237e
Create Date: 2026-05-12 12:30:00.488544

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1fff358fd7e'
down_revision: Union[str, None] = ('b8c4a9f2d3e1', 'ce5737ef237e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
