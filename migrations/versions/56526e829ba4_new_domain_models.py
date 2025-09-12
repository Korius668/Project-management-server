"""New domain models

Revision ID: 56526e829ba4
Revises: 595f35b4d1e0
Create Date: 2025-09-10 14:14:26.456202

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "56526e829ba4"
down_revision: Union[str, Sequence[str], None] = "595f35b4d1e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
