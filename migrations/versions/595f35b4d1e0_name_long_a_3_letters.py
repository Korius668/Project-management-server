"""name long a 3 letters

Revision ID: 595f35b4d1e0
Revises: 41861284331d
Create Date: 2025-08-29 22:56:40.591024

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "595f35b4d1e0"
down_revision: Union[str, Sequence[str], None] = "41861284331d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
