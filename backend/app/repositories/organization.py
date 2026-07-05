from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.organization import Organization

class OrganizationRepository(BaseRepository[Organization]):
    """
    Organization repository to handle CRUD and query operations for Organizations.
    """
    def __init__(self, db: Session):
        super().__init__(db, Organization)

    def get_by_name(self, name: str) -> Optional[Organization]:
        """Fetch organization by exact name."""
        return self.db.query(Organization).filter(Organization.name == name).first()
