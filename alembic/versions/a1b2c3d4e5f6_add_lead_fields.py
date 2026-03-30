"""add phone, location, service_interest, additional_fields columns

Revision ID: a1b2c3d4e5f6
Revises: 42a9ad35056a
Create Date: 2026-03-29 08:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "42a9ad35056a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("leads", sa.Column("phone", sa.String(length=50), nullable=True))
    op.add_column("leads", sa.Column("location", sa.String(length=255), nullable=True))
    op.add_column(
        "leads", sa.Column("service_interest", sa.String(length=500), nullable=True)
    )
    op.add_column("leads", sa.Column("additional_fields", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("leads", "additional_fields")
    op.drop_column("leads", "service_interest")
    op.drop_column("leads", "location")
    op.drop_column("leads", "phone")
