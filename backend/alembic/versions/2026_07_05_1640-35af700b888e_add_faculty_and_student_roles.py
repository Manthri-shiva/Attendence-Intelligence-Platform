"""add_faculty_and_student_roles

Revision ID: 35af700b888e
Revises: e277f834c838
Create Date: 2026-07-05 16:40:02.560330

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
# No custom imports

# revision identifiers, used by Alembic.
revision: str = '35af700b888e'
down_revision: Union[str, None] = 'e277f834c838'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'Faculty'")
        op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'Student'")


def downgrade() -> None:
    pass
