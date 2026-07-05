from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional
from app.schemas.session import SimpleUserResponse

class SimpleSessionRef(BaseModel):
    id: int
    name: str
    session_type: str
    date: date # date representation

    class Config:
        from_attributes = True

class AttendanceBase(BaseModel):
    status: str = Field(default="Absent", description="Present, Late, Absent, Excused")
    gps_status: Optional[str] = None
    verification_status: Optional[str] = None
    activity_status: Optional[str] = None

class AttendanceSubmit(AttendanceBase):
    member_id: int
    session_id: int
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    duration: Optional[int] = None

class AttendanceResponse(AttendanceBase):
    id: int
    member_id: int
    session_id: int
    check_in_time: Optional[datetime]
    check_out_time: Optional[datetime]
    duration: Optional[int]
    
    # AI Verification Metadata
    verification_method: Optional[str] = None
    provider_name: Optional[str] = None
    confidence_score: Optional[float] = None
    liveness_score: Optional[float] = None
    verification_duration: Optional[float] = None
    verification_timestamp: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime
    
    member: Optional[SimpleUserResponse] = None
    session: Optional[SimpleSessionRef] = None

    class Config:
        from_attributes = True

class CheckInResponseGPS(BaseModel):
    latitude: float
    longitude: float

class CheckInResponse(BaseModel):
    attendance_id: int
    image_path: Optional[str] = None
    gps: Optional[CheckInResponseGPS] = None
    verification_status: Optional[str] = None
    timestamp: str

    # backwards compatibility
    id: Optional[int] = None
    status: Optional[str] = None
    gps_status: Optional[str] = None
    confidence_score: Optional[float] = None
    liveness_score: Optional[float] = None
    check_in_time: Optional[datetime] = None
    verification_method: Optional[str] = None
    provider_name: Optional[str] = None

    class Config:
        from_attributes = True
