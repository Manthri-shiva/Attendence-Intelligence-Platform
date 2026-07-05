from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from app.repositories.base import BaseRepository
from app.models.department import Department

class DepartmentRepository(BaseRepository[Department]):
    """
    Department repository to handle CRUD operations on departments.
    """
    def __init__(self, db: Session):
        super().__init__(db, Department)

    def get_by_name_and_org(self, name: str, organization_id: int) -> Optional[Department]:
        """Query department by name within a specific organization."""
        return self.db.query(Department).filter(
            Department.name == name,
            Department.organization_id == organization_id
        ).first()

    def get_by_org(self, organization_id: int, skip: int = 0, limit: int = 100) -> List[Department]:
        """Fetch departments for a specific organization with joined load for head and coordinator."""
        return self.db.query(Department).options(
            joinedload(Department.head),
            joinedload(Department.coordinator)
        ).filter(
            Department.organization_id == organization_id
        ).offset(skip).limit(limit).all()

    def get_all_with_relations(self, skip: int = 0, limit: int = 100) -> List[Department]:
        """Fetch all departments with head and coordinator relationships loaded (prevents N+1)."""
        return self.db.query(Department).options(
            joinedload(Department.head),
            joinedload(Department.coordinator)
        ).offset(skip).limit(limit).all()
