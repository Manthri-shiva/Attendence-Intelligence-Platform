from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole

# Basic nested references to prevent circular dependencies
class OrgRef(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class DeptRef(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class TeamRef(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool = True
    phone: Optional[str] = Field(None, max_length=50)
    gender: Optional[str] = Field(None, max_length=20)
    organization_id: Optional[int] = None
    department_id: Optional[int] = None
    team_id: Optional[int] = None
    emergency_contact: Optional[str] = Field(None, max_length=255)
    joining_date: Optional[date] = None
    status: Optional[str] = Field("Active", max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    phone: Optional[str] = Field(None, max_length=50)
    gender: Optional[str] = Field(None, max_length=20)
    organization_id: Optional[int] = None
    department_id: Optional[int] = None
    team_id: Optional[int] = None
    emergency_contact: Optional[str] = Field(None, max_length=255)
    joining_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, min_length=8)

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    phone: Optional[str]
    gender: Optional[str]
    organization_id: Optional[int]
    department_id: Optional[int]
    team_id: Optional[int]
    emergency_contact: Optional[str]
    joining_date: Optional[date]
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Eager Loaded Refs
    organization: Optional[OrgRef] = None
    department: Optional[DeptRef] = None
    team: Optional[TeamRef] = None

    class Config:
        from_attributes = True
