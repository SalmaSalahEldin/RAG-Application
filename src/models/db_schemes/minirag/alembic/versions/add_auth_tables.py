"""Add authentication tables

Revision ID: add_auth_tables
Revises: fee4cd54bd38
Create Date: 2024-12-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_auth_tables'
down_revision: Union[str, None] = 'fee4cd54bd38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('user_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_uuid', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_superuser', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('user_uuid'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Create query_logs table
    op.create_table('query_logs',
        sa.Column('log_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('log_uuid', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('llm_response', sa.Text(), nullable=False),
        sa.Column('response_time_ms', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('log_id'),
        sa.UniqueConstraint('log_uuid'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], )
    )
    op.create_index('ix_query_logs_user_id', 'query_logs', ['user_id'], unique=False)
    op.create_index('ix_query_logs_created_at', 'query_logs', ['created_at'], unique=False)
    
    # Add user_id to projects table
    op.add_column('projects', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_projects_user_id', 'projects', 'users', ['user_id'], ['user_id'])
    op.create_index('ix_projects_user_id', 'projects', ['user_id'], unique=False)


def downgrade() -> None:
    # Remove user_id from projects table
    op.drop_index('ix_projects_user_id', table_name='projects')
    op.drop_constraint('fk_projects_user_id', 'projects', type_='foreignkey')
    op.drop_column('projects', 'user_id')
    
    # Drop query_logs table
    op.drop_index('ix_query_logs_created_at', table_name='query_logs')
    op.drop_index('ix_query_logs_user_id', table_name='query_logs')
    op.drop_table('query_logs')
    
    # Drop users table
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users') 