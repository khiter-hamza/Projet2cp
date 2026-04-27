"""add_session_budget

Revision ID: a83f8d67f2d1
Revises: 7b3c115de699
Create Date: 2026-04-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a83f8d67f2d1"
down_revision: Union[str, None] = "7b3c115de699"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("budget", sa.Float(), nullable=False, server_default="0"),
    )
    op.alter_column("sessions", "budget", server_default=None)


def downgrade() -> None:
    op.drop_column("sessions", "budget")
