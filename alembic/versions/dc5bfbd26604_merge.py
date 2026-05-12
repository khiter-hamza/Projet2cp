"""merge

Revision ID: dc5bfbd26604
Revises: a1fff358fd7e
Create Date: 2026-05-12 12:48:38.646312

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc5bfbd26604'
down_revision: Union[str, None] = 'a1fff358fd7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
