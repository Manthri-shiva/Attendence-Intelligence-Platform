from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories.organization import OrganizationRepository
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.core.domain_exceptions import DuplicateRecordError, ObjectNotFoundError
from app.services.audit_log import AuditLogService

class OrganizationService:
    """
    Business logic layer for managing Organizations.
    """
    def __init__(self, org_repo: OrganizationRepository):
        self.org_repo = org_repo

    def get_org_by_id(self, org_id: int) -> Optional[Organization]:
        """Fetch organization by id."""
        return self.org_repo.get_by_id(org_id)

    def get_all_orgs(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Fetch all organizations with pagination."""
        return self.org_repo.get_all(skip=skip, limit=limit)

    def search_orgs(self, query: str, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Fetch organizations matching query term."""
        return self.org_repo.db.query(Organization).filter(
            (Organization.name.ilike(f"%{query}%")) |
            (Organization.email.ilike(f"%{query}%"))
        ).offset(skip).limit(limit).all()

    def count_orgs(self, query: Optional[str] = None) -> int:
        """Count total organizations matching query for pagination."""
        q = self.org_repo.db.query(Organization)
        if query:
            q = q.filter(
                (Organization.name.ilike(f"%{query}%")) |
                (Organization.email.ilike(f"%{query}%"))
            )
        return q.count()

    def create_org(self, db: Session, org_in: OrganizationCreate, actor_id: Optional[int]) -> Organization:
        """Create a new organization, checking for name duplication and writing an audit log."""
        # Validation for duplicate organization name
        existing = self.org_repo.get_by_name(org_in.name)
        if existing:
            raise DuplicateRecordError(f"An organization with the name '{org_in.name}' already exists.")

        org_dict = org_in.model_dump()
        new_org = self.org_repo.create(org_dict)

        # Audit Logging
        AuditLogService.log_event(
            db=db,
            actor_id=actor_id,
            action="Create",
            module="Organization",
            new_value=f"ID: {new_org.id}, Name: {new_org.name}",
            reason="Organization created via Admin Portal"
        )
        return new_org

    def update_org(self, db: Session, org_id: int, org_in: OrganizationUpdate, actor_id: Optional[int]) -> Organization:
        """Update organization, validating unique name constraint and logging change."""
        org = self.org_repo.get_by_id(org_id)
        if not org:
            raise ObjectNotFoundError(f"Organization with ID {org_id} not found.")

        org_in_dict = org_in.model_dump(exclude_unset=True)

        if "name" in org_in_dict and org_in_dict["name"] != org.name:
            # Validate duplicate name
            existing = self.org_repo.get_by_name(org_in_dict["name"])
            if existing:
                raise DuplicateRecordError(f"An organization with the name '{org_in_dict['name']}' already exists.")

        old_val = f"Name: {org.name}, Status: {org.status}"
        updated_org = self.org_repo.update(org, org_in_dict)

        # Audit Logging
        AuditLogService.log_event(
            db=db,
            actor_id=actor_id,
            action="Update",
            module="Organization",
            old_value=old_val,
            new_value=f"Name: {updated_org.name}, Status: {updated_org.status}",
            reason="Organization details updated"
        )
        return updated_org

    def delete_org(self, db: Session, org_id: int, actor_id: Optional[int]) -> Organization:
        """Delete an organization (hard/soft-delete based on constraints) and write audit log."""
        org = self.org_repo.get_by_id(org_id)
        if not org:
            raise ObjectNotFoundError(f"Organization with ID {org_id} not found.")

        # Let's perform a soft delete by marking it inactive, or standard delete.
        # The prompt says: "Soft delete if appropriate. Status is 'Active' in models."
        # Let's support soft delete by updating status = "Inactive" (or "Deleted") to preserve integrity.
        old_val = f"Name: {org.name}, Status: {org.status}"
        org_in_dict = {"status": "Inactive"}
        deleted_org = self.org_repo.update(org, org_in_dict)

        # Audit Logging
        AuditLogService.log_event(
            db=db,
            actor_id=actor_id,
            action="Deactivate",
            module="Organization",
            old_value=old_val,
            new_value=f"Status: {deleted_org.status}",
            reason="Organization soft-deleted (status marked Inactive)"
        )
        return deleted_org
