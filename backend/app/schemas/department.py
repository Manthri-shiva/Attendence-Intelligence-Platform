from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.user import UserResponse

class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    organization_id: int
    head_id: Optional[int] = None
    coordinator_id: Optional[int] = None
    status: Optional[str] = Field("Active", max_length=50)

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    organization_id: Optional[int] = None
    head_id: Optional[int] = None
    coordinator_id: Optional[int] = None
    status: Optional[str] = Field(None, max_length=50)

class SimpleUserRef(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True

class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    organization_id: int
    head_id: Optional[int]
    coordinator_id: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    
    # We load head and coordinator optionally
    head: Optional[SimpleUserRef] = None
    coordinator: Optional[SimpleUserRef] = None

    class Config:
        from_attributes = True
