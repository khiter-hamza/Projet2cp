"""add_visa_document_type

Revision ID: d4a2c8f1b9e0
Revises: b8c4a9f2d3e1, ce5737ef237e
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d4a2c8f1b9e0"
down_revision: Union[str, Sequence[str], None] = ("b8c4a9f2d3e1", "ce5737ef237e")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE documents_type ADD VALUE IF NOT EXISTS 'visa'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely without rebuilding the enum.
    pass
