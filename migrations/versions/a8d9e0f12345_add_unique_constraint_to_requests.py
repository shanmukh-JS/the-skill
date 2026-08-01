"""Add unique constraint to requests

Revision ID: a8d9e0f12345
Revises: 6aa8f988907f
Create Date: 2026-08-01 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a8d9e0f12345'
down_revision = '6aa8f988907f'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('requests', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_pending_request', ['sender_id', 'receiver_id', 'skill_id', 'status'])

def downgrade():
    with op.batch_alter_table('requests', schema=None) as batch_op:
        batch_op.drop_constraint('uq_pending_request', type_='unique')
