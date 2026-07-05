from sqlalchemy import Column, Integer, String, Text, Date, Time, Float, ForeignKey, DateTime, Table, func
from sqlalchemy.orm import relationship
from app.core.database import Base

# Association table for session members (many-to-many relationship between Session and User)
session_members = Table(
    "session_members",
    Base.metadata,
    Column("session_id", Integer, ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    session_type = Column(String(100), nullable=False) # e.g. "Lecture", "Meeting", "Lab"
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    grace_time = Column(Integer, nullable=False, default=15) # grace time in minutes
    checkout_time = Column(Time, nullable=True)
    venue = Column(String(255), nullable=True)
    gps_radius = Column(Float, nullable=True) # in meters
    evidence_type = Column(String(100), nullable=True) # "GPS", "Face", "None"
    coordinator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="Draft") # "Draft", "Scheduled", "Active", "Paused", "Completed", "Cancelled", "Archived"
    
    # Geofence & Participant Bounds
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    capacity = Column(Integer, nullable=True)
    face_confidence_threshold = Column(Float, nullable=True, default=0.85)
    fallback_policy = Column(String(100), nullable=True, default="Block")
    
    # Recurrence Fields (for future scheduling extensions)
    recurrence_pattern = Column(String(100), nullable=True)
    recurrence_end_date = Column(Date, nullable=True)
    
    # Lifecycle Transition Timestamps
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    paused_at = Column(DateTime, nullable=True)
    resumed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="sessions")
    department = relationship("Department", back_populates="sessions")
    coordinator = relationship("User", foreign_keys=[coordinator_id])
    assigned_members = relationship("User", secondary=session_members, back_populates="sessions")
    attendances = relationship("Attendance", back_populates="session", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="session", cascade="all, delete-orphan")
