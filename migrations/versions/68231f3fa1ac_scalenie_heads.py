"""Scalenie heads

Revision ID: 68231f3fa1ac
Revises: 2244123344e5, 56526e829ba4
Create Date: 2025-09-11 11:27:27.034887

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68231f3fa1ac'
down_revision: Union[str, Sequence[str], None] = ('2244123344e5', '56526e829ba4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
