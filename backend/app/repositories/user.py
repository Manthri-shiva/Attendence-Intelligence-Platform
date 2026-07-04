from typing import Optional
from sqlalchemy.orm import Session
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
