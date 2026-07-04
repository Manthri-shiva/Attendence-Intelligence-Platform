from typing import Optional, List
from app.repositories.user import UserRepository
from app.models.user import User

class UserService:
    """
    User business logic service layer.
    """
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Fetch user by primary key."""
        return self.user_repo.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Fetch user by email."""
        return self.user_repo.get_by_email(email)

    def update_user_password(self, email: str, new_hashed_password: str) -> bool:
        """Hash and update the password for a user account."""
        user = self.user_repo.get_by_email(email)
        if not user:
            return False
        self.user_repo.update(user, {"hashed_password": new_hashed_password})
        return True
