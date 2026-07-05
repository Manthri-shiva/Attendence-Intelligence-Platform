"""add_session_geofence_and_capacity_and_timestamps

Revision ID: c67508a3b64f
Revises: 35af700b888e
Create Date: 2026-07-05 17:02:20.593419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
# No custom imports

# revision identifiers, used by Alembic.
revision: str = 'c67508a3b64f'
down_revision: Union[str, None] = '35af700b888e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sessions', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('sessions', sa.Column('longitude', sa.Float(), nullable=True))
    op.add_column('sessions', sa.Column('capacity', sa.Integer(), nullable=True))
    op.add_column('sessions', sa.Column('recurrence_pattern', sa.String(100), nullable=True))
    op.add_column('sessions', sa.Column('recurrence_end_date', sa.Date(), nullable=True))
    op.add_column('sessions', sa.Column('scheduled_at', sa.DateTime(), nullable=True))
    op.add_column('sessions', sa.Column('started_at', sa.DateTime(), nullable=True))
    op.add_column('sessions', sa.Column('paused_at', sa.DateTime(), nullable=True))
    op.add_column('sessions', sa.Column('resumed_at', sa.DateTime(), nullable=True))
    op.add_column('sessions', sa.Column('completed_at', sa.DateTime(), nullable=True))
    op.add_column('sessions', sa.Column('archived_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('sessions', 'archived_at')
    op.drop_column('sessions', 'completed_at')
    op.drop_column('sessions', 'resumed_at')
    op.drop_column('sessions', 'paused_at')
    op.drop_column('sessions', 'started_at')
    op.drop_column('sessions', 'scheduled_at')
    op.drop_column('sessions', 'recurrence_end_date')
    op.drop_column('sessions', 'recurrence_pattern')
    op.drop_column('sessions', 'capacity')
    op.drop_column('sessions', 'longitude')
    op.drop_column('sessions', 'latitude')
