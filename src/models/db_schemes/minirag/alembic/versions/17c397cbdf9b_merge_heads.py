"""merge heads

Revision ID: 17c397cbdf9b
Revises: add_auth_tables, add_project_code
Create Date: 2025-08-05 19:47:19.243088

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17c397cbdf9b'
down_revision: Union[str, None] = ('add_auth_tables', 'add_project_code')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
