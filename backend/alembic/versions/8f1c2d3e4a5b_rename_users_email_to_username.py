"""rename users.email to username

Revision ID: 8f1c2d3e4a5b
Revises: 25bf5de0a89a
Create Date: 2026-09-17 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f1c2d3e4a5b'
down_revision: Union[str, Sequence[str], None] = '25bf5de0a89a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.alter_column('users', 'email', new_column_name='username', existing_type=sa.String(length=255))
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.alter_column('users', 'username', new_column_name='email', existing_type=sa.String(length=255))
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
