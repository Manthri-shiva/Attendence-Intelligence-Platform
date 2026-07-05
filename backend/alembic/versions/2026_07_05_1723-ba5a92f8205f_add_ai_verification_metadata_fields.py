"""add_ai_verification_metadata_fields

Revision ID: ba5a92f8205f
Revises: c67508a3b64f
Create Date: 2026-07-05 17:23:56.892977

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
# No custom imports

# revision identifiers, used by Alembic.
revision: str = 'ba5a92f8205f'
down_revision: Union[str, None] = 'c67508a3b64f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add fields to sessions table
    op.add_column('sessions', sa.Column('face_confidence_threshold', sa.Float(), nullable=True, server_default='0.85'))
    op.add_column('sessions', sa.Column('fallback_policy', sa.String(length=100), nullable=True, server_default='Block'))
    
    # 2. Add fields to attendances table
    op.add_column('attendances', sa.Column('verification_method', sa.String(length=100), nullable=True))
    op.add_column('attendances', sa.Column('provider_name', sa.String(length=100), nullable=True))
    op.add_column('attendances', sa.Column('confidence_score', sa.Float(), nullable=True))
    op.add_column('attendances', sa.Column('liveness_score', sa.Float(), nullable=True))
    op.add_column('attendances', sa.Column('verification_duration', sa.Float(), nullable=True))
    op.add_column('attendances', sa.Column('verification_timestamp', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # 1. Drop fields from attendances
    op.drop_column('attendances', 'verification_timestamp')
    op.drop_column('attendances', 'verification_duration')
    op.drop_column('attendances', 'liveness_score')
    op.drop_column('attendances', 'confidence_score')
    op.drop_column('attendances', 'provider_name')
    op.drop_column('attendances', 'verification_method')
    
    # 2. Drop fields from sessions
    op.drop_column('sessions', 'fallback_policy')
    op.drop_column('sessions', 'face_confidence_threshold')
