import re
from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories.user import UserRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.department import DepartmentRepository
from app.repositories.team import TeamRepository
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash
from app.core.domain_exceptions import DuplicateRecordError, ObjectNotFoundError, PermissionDeniedError
from app.services.audit_log import AuditLogService

PHONE_REGEX = re.compile(r"^\+?[0-9\-\s\(\)]{7,25}$")

class UserService:
    """
    User business logic service layer with validation, filtering, and audit trail hooks.
    """
    def __init__(
        self,
        user_repo: UserRepository,
        org_repo: Optional[OrganizationRepository] = None,
        dept_repo: Optional[DepartmentRepository] = None,
        team_repo: Optional[TeamRepository] = None
    ):
        self.user_repo = user_repo
        self.org_repo = org_repo
        self.dept_repo = dept_repo
        self.team_repo = team_repo

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Fetch user by primary key."""
        return self.user_repo.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Fetch user by email."""
        return self.user_repo.get_by_email(email)

    def get_users_list(
        self,
        organization_id: Optional[int] = None,
        department_id: Optional[int] = None,
        team_id: Optional[int] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Fetch a paginated list of users filtered by scopes, roles, status, and text search."""
        return self.user_repo.get_users_filtered(
            organization_id=organization_id,
            department_id=department_id,
            team_id=team_id,
            role=role,
            status=status,
            search_query=search_query,
            skip=skip,
            limit=limit
        )

    def get_users_count(
        self,
        organization_id: Optional[int] = None,
        department_id: Optional[int] = None,
        team_id: Optional[int] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> int:
        """Count total users matching filters."""
        return self.user_repo.count_users_filtered(
            organization_id=organization_id,
            department_id=department_id,
            team_id=team_id,
            role=role,
            status=status,
            search_query=search_query
        )

    def update_user_password(self, email: str, new_hashed_password: str) -> bool:
        """Hash and update the password for a user account."""
        user = self.user_repo.get_by_email(email)
        if not user:
            return False
        self.user_repo.update(user, {"hashed_password": new_hashed_password})
        return True

    def _validate_profile_relations_and_format(self, org_id: Optional[int], dept_id: Optional[int], team_id: Optional[int], phone: Optional[str]):
        """Validate linked entities existence and format constraints."""
        # 1. Phone number format validation
        if phone:
            if not PHONE_REGEX.match(phone):
                raise ValueError("Invalid phone number format. Provide a valid digits sequence.")

        # 2. Check Organization existence
        if org_id and self.org_repo:
            org = self.org_repo.get_by_id(org_id)
            if not org:
                raise ObjectNotFoundError(f"Organization with ID {org_id} does not exist.")

        # 3. Check Department existence
        if dept_id and self.dept_repo:
            dept = self.dept_repo.get_by_id(dept_id)
            if not dept:
                raise ObjectNotFoundError(f"Department with ID {dept_id} does not exist.")
            # If org_id is also supplied, verify department belongs to it
            if org_id and dept.organization_id != org_id:
                raise ValueError(f"Department ID {dept_id} does not belong to Organization ID {org_id}.")

        # 4. Check Team existence
        if team_id and self.team_repo:
            team = self.team_repo.get_by_id(team_id)
            if not team:
                raise ObjectNotFoundError(f"Team with ID {team_id} does not exist.")
            # Verify team belongs to department
            if dept_id and team.department_id != dept_id:
                raise ValueError(f"Team ID {team_id} does not belong to Department ID {dept_id}.")

    def create_user(self, db: Session, user_in: UserCreate, actor_id: Optional[int]) -> User:
        """Create a new user, hashing password, checking duplications, and writing audit log."""
        # Check email uniqueness
        existing_user = self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise DuplicateRecordError(f"A user with email '{user_in.email}' already exists.")

        # Validate linked entities and phone formats
        try:
            self._validate_profile_relations_and_format(
                user_in.organization_id, user_in.department_id, user_in.team_id, user_in.phone
            )
        except ValueError as val_err:
            raise DuplicateRecordError(str(val_err)) # Handled as 400

        # Model Dump and Hash password
        user_dict = user_in.model_dump()
        raw_pwd = user_dict.pop("password")
        user_dict["hashed_password"] = get_password_hash(raw_pwd)

        new_user = self.user_repo.create(user_dict)

        # Audit Logging
        AuditLogService.log_event(
            db=db,
            actor_id=actor_id,
            action="Create",
            module="User",
            new_value=f"ID: {new_user.id}, Email: {new_user.email}, Role: {new_user.role}",
            reason="User registered via portal admin flow"
        )
        return new_user

    def update_user(self, db: Session, user_id: int, user_in: UserUpdate, actor_id: Optional[int]) -> User:
        """Update user profile fields, verifying relations, and logging changes."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ObjectNotFoundError(f"User with ID {user_id} not found.")

        user_in_dict = user_in.model_dump(exclude_unset=True)

        # Email uniqueness check
        new_email = user_in_dict.get("email")
        if new_email and new_email.lower() != user.email.lower():
            existing = self.user_repo.get_by_email(new_email)
            if existing and existing.id != user.id:
                raise DuplicateRecordError(f"A user with email '{new_email}' already exists.")

        # Validate linked entities and formats
        target_org = user_in_dict.get("organization_id", user.organization_id)
        target_dept = user_in_dict.get("department_id", user.department_id)
        target_team = user_in_dict.get("team_id", user.team_id)
        target_phone = user_in_dict.get("phone", user.phone)

        try:
            self._validate_profile_relations_and_format(target_org, target_dept, target_team, target_phone)
        except ValueError as val_err:
            raise DuplicateRecordError(str(val_err))

        # Handle password update if passed
        if "password" in user_in_dict:
            raw_pwd = user_in_dict.pop("password")
            if raw_pwd:
                user_in_dict["hashed_password"] = get_password_hash(raw_pwd)

        old_val = f"Name: {user.full_name}, Email: {user.email}, Active: {user.is_active}, Role: {user.role}"
        updated_user = self.user_repo.update(user, user_in_dict)

        # Audit Logging
        AuditLogService.log_event(
            db=db,
            actor_id=actor_id,
            action="Update",
            module="User",
            old_value=old_val,
            new_value=f"Name: {updated_user.full_name}, Email: {updated_user.email}, Active: {updated_user.is_active}",
            reason="User profile updated"
        )
        return updated_user

    def deactivate_user(self, db: Session, user_id: int, actor_id: Optional[int]) -> User:
        """Deactivate a user account, setting is_active = False and logging event."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ObjectNotFoundError(f"User with ID {user_id} not found.")

        old_val = f"Email: {user.email}, Active: {user.is_active}"
        updated_user = self.user_repo.update(user, {"is_active": False, "status": "Inactive"})

        # Audit Logging
        AuditLogService.log_event(
            db=db,
            actor_id=actor_id,
            action="Deactivate",
            module="User",
            old_value=old_val,
            new_value=f"Active: {updated_user.is_active}, Status: {updated_user.status}",
            reason="User account deactivated"
        )
        return updated_user

    def activate_user(self, db: Session, user_id: int, actor_id: Optional[int]) -> User:
        """Activate a user account, setting is_active = True and logging event."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ObjectNotFoundError(f"User with ID {user_id} not found.")

        old_val = f"Email: {user.email}, Active: {user.is_active}"
        updated_user = self.user_repo.update(user, {"is_active": True, "status": "Active"})

        # Audit Logging
        AuditLogService.log_event(
            db=db,
            actor_id=actor_id,
            action="Activate",
            module="User",
            old_value=old_val,
            new_value=f"Active: {updated_user.is_active}, Status: {updated_user.status}",
            reason="User account activated"
        )
        return updated_user
