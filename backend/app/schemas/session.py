from pydantic import BaseModel, Field
from datetime import date, time, datetime
from typing import Optional, List

# Simple nested objects for responses
class SimpleUserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str

    class Config:
        from_attributes = True

class SimpleDeptResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class SimpleOrgResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class SessionBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    session_type: str = Field(..., description="e.g. Lecture, Lab, Workshop, Meeting, Seminar, Examination, Training")
    date: date
    start_time: time
    end_time: time
    grace_time: int = Field(default=15)
    checkout_time: Optional[time] = None
    venue: Optional[str] = Field(default=None, max_length=255)
    gps_radius: Optional[float] = Field(default=None) # in meters
    evidence_type: Optional[str] = Field(default="GPS", description="GPS, Face, QR, Manual, Hybrid")
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)
    capacity: Optional[int] = Field(default=None)
    recurrence_pattern: Optional[str] = Field(default=None, max_length=100)
    recurrence_end_date: Optional[date] = Field(default=None)
    face_confidence_threshold: Optional[float] = Field(default=0.85)
    fallback_policy: Optional[str] = Field(default="Block", description="Block, CoordinatorApproval, QR")

class SessionCreate(SessionBase):
    coordinator_id: Optional[int] = None
    department_id: Optional[int] = None
    organization_id: int

class SessionUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    session_type: Optional[str] = None
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    grace_time: Optional[int] = None
    checkout_time: Optional[time] = None
    venue: Optional[str] = Field(default=None, max_length=255)
    gps_radius: Optional[float] = None
    evidence_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity: Optional[int] = None
    recurrence_pattern: Optional[str] = Field(default=None, max_length=100)
    recurrence_end_date: Optional[date] = None
    coordinator_id: Optional[int] = None
    department_id: Optional[int] = None
    status: Optional[str] = None
    face_confidence_threshold: Optional[float] = None
    fallback_policy: Optional[str] = None

class SessionResponse(SessionBase):
    id: int
    coordinator_id: Optional[int]
    department_id: Optional[int]
    organization_id: int
    status: str
    
    # State timestamps
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    paused_at: Optional[datetime]
    resumed_at: Optional[datetime]
    completed_at: Optional[datetime]
    archived_at: Optional[datetime]
    
    created_at: datetime
    updated_at: datetime

    coordinator: Optional[SimpleUserResponse] = None
    department: Optional[SimpleDeptResponse] = None
    organization: Optional[SimpleOrgResponse] = None
    assigned_members: List[SimpleUserResponse] = []

    class Config:
        from_attributes = True

class SessionAssignMembers(BaseModel):
    user_ids: List[int]

class CheckInRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    captured_at: Optional[str] = None
    session_id: Optional[int] = None
    image_b64: Optional[str] = None
    simulate_confidence: Optional[float] = None
    simulate_liveness: Optional[str] = None
    verification_status: Optional[str] = "Verified"
    gps_status: Optional[str] = "Verified"

class CheckOutRequest(BaseModel):
    latitude: float
    longitude: float
    verification_status: Optional[str] = "Verified"
    gps_status: Optional[str] = "Verified"
