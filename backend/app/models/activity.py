from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True) # e.g. "Research", "Development"
    priority = Column(String(50), nullable=False, default="Medium") # e.g. "Low", "Medium", "High"
    assigned_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="Pending") # "Pending", "In Progress", "Completed", "Reviewed"
    remarks = Column(Text, nullable=True)
    evidence = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    assigned_by = relationship("User", foreign_keys=[assigned_by_id], back_populates="created_activities")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_activities")
    session = relationship("Session", back_populates="activities")
    department = relationship("Department", back_populates="activities")
