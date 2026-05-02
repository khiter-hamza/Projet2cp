"""Change application destination country to string

Revision ID: b8c4a9f2d3e1
Revises: 793f95191769
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8c4a9f2d3e1"
down_revision: Union[str, None] = "793f95191769"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "applications",
        "destination_country",
        existing_type=sa.Enum(
            "algerie",
            "france",
            "allemagne",
            "tunisie",
            name="countries",
        ),
        type_=sa.String(length=100),
        existing_nullable=True,
        postgresql_using="destination_country::text",
    )


def downgrade() -> None:
    countries_enum = sa.Enum(
        "algerie",
        "france",
        "allemagne",
        "tunisie",
        name="countries",
    )
    countries_enum.create(op.get_bind(), checkfirst=True)
    op.alter_column(
        "applications",
        "destination_country",
        existing_type=sa.String(length=100),
        type_=countries_enum,
        existing_nullable=True,
        postgresql_using="destination_country::countries",
    )
