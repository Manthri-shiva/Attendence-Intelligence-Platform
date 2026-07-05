from typing import Optional
from sqlalchemy.orm import Session, joinedload
from app.repositories.base import BaseRepository
from app.models.user import User

class UserRepository(BaseRepository[User]):
    """
    User specific repository for database operations on the users table.
    """
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> Optional[User]:
        """Query user by unique email address."""
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_users_filtered(
        self,
        organization_id: Optional[int] = None,
        department_id: Optional[int] = None,
        team_id: Optional[int] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[User]:
        """Query users with pagination, text-search, and multiple relationship filters."""
        query = self.db.query(User).options(
            joinedload(User.organization),
            joinedload(User.department),
            joinedload(User.team)
        )
        if organization_id is not None:
            query = query.filter(User.organization_id == organization_id)
        if department_id is not None:
            query = query.filter(User.department_id == department_id)
        if team_id is not None:
            query = query.filter(User.team_id == team_id)
        if role is not None:
            query = query.filter(User.role == role)
        if status is not None:
            query = query.filter(User.status == status)
        if search_query:
            term = f"%{search_query.lower()}%"
            query = query.filter(
                (User.full_name.ilike(term)) |
                (User.email.ilike(term)) |
                (User.phone.ilike(term))
            )
        
        # Sort users by ID ascending by default
        return query.order_by(User.id.asc()).offset(skip).limit(limit).all()

    def count_users_filtered(
        self,
        organization_id: Optional[int] = None,
        department_id: Optional[int] = None,
        team_id: Optional[int] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> int:
        """Count total matching users for pagination headers."""
        query = self.db.query(User)
        if organization_id is not None:
            query = query.filter(User.organization_id == organization_id)
        if department_id is not None:
            query = query.filter(User.department_id == department_id)
        if team_id is not None:
            query = query.filter(User.team_id == team_id)
        if role is not None:
            query = query.filter(User.role == role)
        if status is not None:
            query = query.filter(User.status == status)
        if search_query:
            term = f"%{search_query.lower()}%"
            query = query.filter(
                (User.full_name.ilike(term)) |
                (User.email.ilike(term)) |
                (User.phone.ilike(term))
            )
        return query.count()
