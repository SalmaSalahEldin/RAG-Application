"""Add project_code field for user-scoped project IDs

Revision ID: add_project_code
Revises: fee4cd54bd38
Create Date: 2025-08-05 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_project_code'
down_revision: Union[str, None] = 'fee4cd54bd38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add project_code column
    op.add_column('projects', sa.Column('project_code', sa.Integer(), nullable=True))
    
    # Set default project_code values for existing projects (using project_id as the code)
    op.execute("UPDATE projects SET project_code = project_id WHERE project_code IS NULL")
    
    # Make project_code not nullable after setting default values
    op.alter_column('projects', 'project_code', nullable=False)
    
    # Add unique constraint for user_id and project_code
    op.create_unique_constraint('_user_project_code_uc', 'projects', ['user_id', 'project_code'])


def downgrade() -> None:
    # Remove unique constraint
    op.drop_constraint('_user_project_code_uc', 'projects', type_='unique')
    
    # Remove project_code column
    op.drop_column('projects', 'project_code') 