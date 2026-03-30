"""add email column

Revision ID: 42a9ad35056a
Revises: 73bcfe3eb80e
Create Date: 2026-03-28 16:45:32.233940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "42a9ad35056a"
down_revision: Union[str, Sequence[str], None] = "73bcfe3eb80e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("leads", sa.Column("email", sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("leads", "email")
