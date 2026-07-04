from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (UniqueConstraint("member_id", "session_id", name="uq_attendances_member_session"),)

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True) # in minutes
    gps_status = Column(String(50), nullable=True) # e.g. "Verified", "Failed", "Pending"
    verification_status = Column(String(50), nullable=True) # e.g. "Verified", "Failed", "Pending"
    activity_status = Column(String(50), nullable=True) # e.g. "Completed", "Pending", "None"
    status = Column(String(50), nullable=False, default="Absent") # e.g. "Present", "Absent", "Late", "Excused"
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    member = relationship("User", back_populates="attendances")
    session = relationship("Session", back_populates="attendances")
