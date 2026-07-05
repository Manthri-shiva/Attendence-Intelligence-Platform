from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class TeamBase(BaseModel):
    name: str = Field(..., max_length=255)
    department_id: int
    leader_id: Optional[int] = None
    status: Optional[str] = Field("Active", max_length=50)

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    department_id: Optional[int] = None
    leader_id: Optional[int] = None
    status: Optional[str] = Field(None, max_length=50)

class SimpleUserRef(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True

class SimpleDeptRef(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class TeamResponse(BaseModel):
    id: int
    name: str
    department_id: int
    leader_id: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    
    leader: Optional[SimpleUserRef] = None
    department: Optional[SimpleDeptRef] = None

    class Config:
        from_attributes = True
