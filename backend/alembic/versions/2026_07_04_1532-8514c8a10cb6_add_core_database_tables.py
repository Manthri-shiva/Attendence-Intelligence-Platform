"""Add core database tables

Revision ID: 8514c8a10cb6
Revises: None
Create Date: 2026-07-04 15:32:02.887395

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8514c8a10cb6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create 'organizations' table (depends on nothing)
    op.create_table('organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('logo', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('timezone', sa.String(length=100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)

    # 2. Create 'departments' table (exclude cyclic users foreign keys head_id/coordinator_id)
    op.create_table('departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('head_id', sa.Integer(), nullable=True),
        sa.Column('coordinator_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_departments_coordinator_id'), 'departments', ['coordinator_id'], unique=False)
    op.create_index(op.f('ix_departments_head_id'), 'departments', ['head_id'], unique=False)
    op.create_index(op.f('ix_departments_id'), 'departments', ['id'], unique=False)
    op.create_index(op.f('ix_departments_organization_id'), 'departments', ['organization_id'], unique=False)

    # 3. Create 'teams' table (exclude cyclic user foreign key leader_id)
    op.create_table('teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('leader_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_teams_department_id'), 'teams', ['department_id'], unique=False)
    op.create_index(op.f('ix_teams_id'), 'teams', ['id'], unique=False)
    op.create_index(op.f('ix_teams_leader_id'), 'teams', ['leader_id'], unique=False)

    # 4. Create 'users' table (exclude cyclic department_id/team_id foreign keys, which we link later)
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('SystemAdmin', 'OrgAdmin', 'Coordinator', 'Member', 'Auditor', name='userrole'), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('profile_photo', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('emergency_contact', sa.String(length=255), nullable=True),
        sa.Column('joining_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_department_id'), 'users', ['department_id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)
    op.create_index(op.f('ix_users_team_id'), 'users', ['team_id'], unique=False)

    # 5. Create 'sessions' table
    op.create_table('sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('session_type', sa.String(length=100), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('grace_time', sa.Integer(), nullable=False),
        sa.Column('checkout_time', sa.Time(), nullable=True),
        sa.Column('venue', sa.String(length=255), nullable=True),
        sa.Column('gps_radius', sa.Float(), nullable=True),
        sa.Column('evidence_type', sa.String(length=100), nullable=True),
        sa.Column('coordinator_id', sa.Integer(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['coordinator_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_coordinator_id'), 'sessions', ['coordinator_id'], unique=False)
    op.create_index(op.f('ix_sessions_department_id'), 'sessions', ['department_id'], unique=False)
    op.create_index(op.f('ix_sessions_id'), 'sessions', ['id'], unique=False)
    op.create_index(op.f('ix_sessions_organization_id'), 'sessions', ['organization_id'], unique=False)

    # 6. Create 'attendances' table
    op.create_table('attendances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('check_in_time', sa.DateTime(), nullable=True),
        sa.Column('check_out_time', sa.DateTime(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('gps_status', sa.String(length=50), nullable=True),
        sa.Column('verification_status', sa.String(length=50), nullable=True),
        sa.Column('activity_status', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['member_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attendances_id'), 'attendances', ['id'], unique=False)
    op.create_index(op.f('ix_attendances_member_id'), 'attendances', ['member_id'], unique=False)
    op.create_index(op.f('ix_attendances_session_id'), 'attendances', ['session_id'], unique=False)

    # 7. Create 'activities' table
    op.create_table('activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=False),
        sa.Column('assigned_by_id', sa.Integer(), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('evidence', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assigned_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activities_assigned_by_id'), 'activities', ['assigned_by_id'], unique=False)
    op.create_index(op.f('ix_activities_assigned_to_id'), 'activities', ['assigned_to_id'], unique=False)
    op.create_index(op.f('ix_activities_department_id'), 'activities', ['department_id'], unique=False)
    op.create_index(op.f('ix_activities_id'), 'activities', ['id'], unique=False)
    op.create_index(op.f('ix_activities_session_id'), 'activities', ['session_id'], unique=False)

    # 8. Create 'session_members' table
    op.create_table('session_members',
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('session_id', 'user_id')
    )

    # 9. Create 'notifications' table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)

    # 10. Create 'reports' table
    op.create_table('reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('report_type', sa.String(length=100), nullable=False),
        sa.Column('format', sa.String(length=50), nullable=False),
        sa.Column('generated_by_id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['generated_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_generated_by_id'), 'reports', ['generated_by_id'], unique=False)
    op.create_index(op.f('ix_reports_id'), 'reports', ['id'], unique=False)

    # 11. Create 'audit_logs' table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('module', sa.String(length=100), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('device', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_actor_id'), 'audit_logs', ['actor_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)

    # 12. Create foreign keys to resolve the cyclic dependencies (now that all tables exist)
    op.create_foreign_key('fk_departments_head_id', 'departments', 'users', ['head_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_departments_coordinator_id', 'departments', 'users', ['coordinator_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_teams_leader_id', 'teams', 'users', ['leader_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_users_department_id', 'users', 'departments', ['department_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_users_team_id', 'users', 'teams', ['team_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    # 1. Drop foreign keys resolving cyclic dependencies first
    op.drop_constraint('fk_users_team_id', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_department_id', 'users', type_='foreignkey')
    op.drop_constraint('fk_teams_leader_id', 'teams', type_='foreignkey')
    op.drop_constraint('fk_departments_coordinator_id', 'departments', type_='foreignkey')
    op.drop_constraint('fk_departments_head_id', 'departments', type_='foreignkey')

    # 2. Drop tables in reverse dependent order
    op.drop_table('session_members')
    op.drop_index(op.f('ix_attendances_session_id'), table_name='attendances')
    op.drop_index(op.f('ix_attendances_member_id'), table_name='attendances')
    op.drop_index(op.f('ix_attendances_id'), table_name='attendances')
    op.drop_table('attendances')
    op.drop_index(op.f('ix_activities_session_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_department_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_assigned_to_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_assigned_by_id'), table_name='activities')
    op.drop_table('activities')
    op.drop_index(op.f('ix_sessions_organization_id'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_id'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_department_id'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_coordinator_id'), table_name='sessions')
    op.drop_table('sessions')
    op.drop_index(op.f('ix_reports_id'), table_name='reports')
    op.drop_index(op.f('ix_reports_generated_by_id'), table_name='reports')
    op.drop_table('reports')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_actor_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_users_team_id'), table_name='users')
    op.drop_index(op.f('ix_users_organization_id'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_department_id'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_teams_leader_id'), table_name='teams')
    op.drop_index(op.f('ix_teams_id'), table_name='teams')
    op.drop_index(op.f('ix_teams_department_id'), table_name='teams')
    op.drop_table('teams')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')
    op.drop_index(op.f('ix_departments_organization_id'), table_name='departments')
    op.drop_index(op.f('ix_departments_id'), table_name='departments')
    op.drop_index(op.f('ix_departments_head_id'), table_name='departments')
    op.drop_index(op.f('ix_departments_coordinator_id'), table_name='departments')
    op.drop_table('departments')

