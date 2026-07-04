from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True
