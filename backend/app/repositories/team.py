from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from app.repositories.base import BaseRepository
from app.models.team import Team

class TeamRepository(BaseRepository[Team]):
    """
    Team repository to handle CRUD and specific query operations for Teams.
    """
    def __init__(self, db: Session):
        super().__init__(db, Team)

    def get_by_name_and_dept(self, name: str, department_id: int) -> Optional[Team]:
        """Query team by name within a specific department."""
        return self.db.query(Team).filter(
            Team.name == name,
            Team.department_id == department_id
        ).first()

    def get_by_dept(self, department_id: int, skip: int = 0, limit: int = 100) -> List[Team]:
        """Fetch teams for a specific department with leader relationship loaded."""
        return self.db.query(Team).options(
            joinedload(Team.leader)
        ).filter(
            Team.department_id == department_id
        ).offset(skip).limit(limit).all()

    def get_all_with_relations(self, skip: int = 0, limit: int = 100) -> List[Team]:
        """Fetch all teams with relationship mappings loaded (prevents N+1)."""
        return self.db.query(Team).options(
            joinedload(Team.leader),
            joinedload(Team.department)
        ).offset(skip).limit(limit).all()
