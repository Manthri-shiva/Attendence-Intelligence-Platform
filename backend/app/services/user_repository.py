from typing import Dict, Optional
from app.models.user import User, UserRole
from app.core.security import get_password_hash

class UserRepository:
    """
    In-memory mock repository for User operations to keep database operations
    abstracted in Milestone 2 without connecting to PostgreSQL.
    """
    def __init__(self):
        self._users_by_email: Dict[str, User] = {}
        self._users_by_id: Dict[int, User] = {}
        self._bootstrap_users()
        
    def _bootstrap_users(self):
        default_users = [
            {
                "id": 1,
                "email": "admin@aip.com",
                "full_name": "System Administrator",
                "role": UserRole.SystemAdmin,
                "password": "password123",
                "is_active": True
            },
            {
                "id": 2,
                "email": "coordinator@aip.com",
                "full_name": "Attendance Coordinator",
                "role": UserRole.Coordinator,
                "password": "password123",
                "is_active": True
            },
            {
                "id": 3,
                "email": "member@aip.com",
                "full_name": "Team Member",
                "role": UserRole.Member,
                "password": "password123",
                "is_active": True
            }
        ]
        for u in default_users:
            user_obj = User(
                id=u["id"],
                email=u["email"],
                full_name=u["full_name"],
                role=u["role"],
                hashed_password=get_password_hash(u["password"]),
                is_active=u["is_active"]
            )
            self._users_by_email[user_obj.email.lower()] = user_obj
            self._users_by_id[user_obj.id] = user_obj
            
    def get_by_email(self, email: str) -> Optional[User]:
        return self._users_by_email.get(email.lower())
        
    def get_by_id(self, id: int) -> Optional[User]:
        return self._users_by_id.get(id)
        
    def update_password(self, email: str, new_hashed_password: str) -> bool:
        user = self.get_by_email(email)
        if user:
            user.hashed_password = new_hashed_password
            return True
        return False

# Export a singleton instance of UserRepository
user_repo = UserRepository()
