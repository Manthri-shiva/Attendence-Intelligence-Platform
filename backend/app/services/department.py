from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories.department import DepartmentRepository
from app.repositories.user import UserRepository
from app.repositories.organization import OrganizationRepository
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.core.domain_exceptions import DuplicateRecordError, ObjectNotFoundError, PermissionDeniedError
from app.services.audit_log import AuditLogService

class DepartmentService:
    """
    Business logic layer for managing Departments.
    """
    def __init__(self, dept_repo: DepartmentRepository, user_repo: UserRepository, org_repo: OrganizationRepository):
        self.dept_repo = dept_repo
        self.user_repo = user_repo
        self.org_repo = org_repo

    def get_dept_by_id(self, dept_id: int) -> Optional[Department]:
        """Fetch department by id."""
        return self.dept_repo.get_by_id(dept_id)

    def get_all_depts(self, skip: int = 0, limit: int = 100) -> List[Department]:
        """Fetch all departments with pagination and eager relationships."""
        return self.dept_repo.get_all_with_relations(skip=skip, limit=limit)

    def get_depts_by_org(self, organization_id: int, skip: int = 0, limit: int = 100) -> List[Department]:
        """Fetch departments filtered by organization."""
        return self.dept_repo.get_by_org(organization_id, skip=skip, limit=limit)

    def search_depts(self, query: str, organization_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Department]:
        """Fetch departments matching search text, optionally scoped to an organization."""
        q = self.dept_repo.db.query(Department)
        if organization_id is not None:
            q = q.filter(Department.organization_id == organization_id)
        q = q.filter(Department.name.ilike(f"%{query}%"))
        return q.offset(skip).limit(limit).all()

    def count_depts(self, query: Optional[str] = None, organization_id: Optional[int] = None) -> int:
        """Count matching departments for pagination."""
        q = self.dept_repo.db.query(Department)
        if organization_id is not None:
            q = q.filter(Department.organization_id == organization_id)
        if query:
            q = q.filter(Department.name.ilike(f"%{query}%"))
        return q.count()

    def create_dept(self, db: Session, dept_in: DepartmentCreate, actor_id: Optional[int]) -> Department:
        """Create department, validating organization, head/coordinator users, duplicate name, and logging audit."""
        # Validate organization exists
        org = self.org_repo.get_by_id(dept_in.organization_id)
        if not org:
            raise ObjectNotFoundError(f"Organization with ID {dept_in.organization_id} does not exist.")

        # Prevent duplicate department name in the same organization
        existing = self.dept_repo.get_by_name_and_org(dept_in.name, dept_in.organization_id)
        if existing:
            raise DuplicateRecordError(f"A department named '{dept_in.name}' already exists in this organization.")

        # Validate head existence if supplied
        if dept_in.head_id:
            head = self.user_repo.get_by_id(dept_in.head_id)
            if not head:
                raise ObjectNotFoundError(f"Department Head User with ID {dept_in.head_id} not found.")

        # Validate coordinator existence if supplied
        if dept_in.coordinator_id:
            coord = self.user_repo.get_by_id(dept_in.coordinator_id)
            if not coord:
                raise ObjectNotFoundError(f"Department Coordinator User with ID {dept_in.coordinator_id} not found.")

        dept_dict = dept_in.model_dump()
        new_dept = self.dept_repo.create(dept_dict)

        # Audit Logging
        AuditLogService.log_event(
            db=db,
            actor_id=actor_id,
            action="Create",
            module="Department",
            new_value=f"ID: {new_dept.id}, Name: {new_dept.name}, OrgID: {new_dept.organization_id}",
            reason="Department created"
        )
        return new_dept

    def update_dept(self, db: Session, dept_id: int, dept_in: DepartmentUpdate, actor_id: Optional[int]) -> Department:
        """Update department configurations, enforcing constraints and logging change."""
        dept = self.dept_repo.get_by_id(dept_id)
        if not dept:
            raise ObjectNotFoundError(f"Department with ID {dept_id} not found.")

        dept_in_dict = dept_in.model_dump(exclude_unset=True)

        # Check duplicate name within organization if name changes
        new_name = dept_in_dict.get("name")
        target_org_id = dept_in_dict.get("organization_id", dept.organization_id)
        
        if (new_name and new_name != dept.name) or (target_org_id != dept.organization_id):
            check_name = new_name or dept.name
            existing = self.dept_repo.get_by_name_and_org(check_name, target_org_id)
            if existing and existing.id != dept.id:
                raise DuplicateRecordError(f"A department named '{check_name}' already exists in the target organization.")

        # Validate head_id & coordinator_id
        if "head_id" in dept_in_dict and dept_in_dict["head_id"] is not None:
            head = self.user_repo.get_by_id(dept_in_dict["head_id"])
            if not head:
                raise ObjectNotFoundError(f"Department Head User with ID {dept_in_dict['head_id']} not found.")
        
        if "coordinator_id" in dept_in_dict and dept_in_dict["coordinator_id"] is not None:
            coord = self.user_repo.get_by_id(dept_in_dict["coordinator_id"])
            if not coord:
                raise ObjectNotFoundError(f"Department Coordinator User with ID {dept_in_dict['coordinator_id']} not found.")

        old_val = f"Name: {dept.name}, OrgID: {dept.organization_id}, HeadID: {dept.head_id}, Status: {dept.status}"
        updated_dept = self.dept_repo.update(dept, dept_in_dict)

        # Audit Logging
        AuditLogService.log_event(
            db=db,
            actor_id=actor_id,
            action="Update",
            module="Department",
            old_value=old_val,
            new_value=f"Name: {updated_dept.name}, HeadID: {updated_dept.head_id}, Status: {updated_dept.status}",
            reason="Department configurations updated"
        )
        return updated_dept

    def delete_dept(self, db: Session, dept_id: int, actor_id: Optional[int]) -> Department:
        """Delete/Deactivate department and write audit log."""
        dept = self.dept_repo.get_by_id(dept_id)
        if not dept:
            raise ObjectNotFoundError(f"Department with ID {dept_id} not found.")

        old_val = f"Name: {dept.name}, Status: {dept.status}"
        updated_dept = self.dept_repo.update(dept, {"status": "Inactive"})

        # Audit Logging
        AuditLogService.log_event(
            db=db,
            actor_id=actor_id,
            action="Deactivate",
            module="Department",
            old_value=old_val,
            new_value=f"Status: {updated_dept.status}",
            reason="Department marked Inactive (soft-deleted)"
        )
        return updated_dept
