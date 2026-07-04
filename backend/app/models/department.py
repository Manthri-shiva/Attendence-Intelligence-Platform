from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    head_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    coordinator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="Active")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="departments")
    head = relationship("User", foreign_keys=[head_id])
    coordinator = relationship("User", foreign_keys=[coordinator_id])
    teams = relationship("Team", back_populates="department", cascade="all, delete-orphan")
    users = relationship("User", back_populates="department", foreign_keys="[User.department_id]")
    sessions = relationship("Session", back_populates="department")
    activities = relationship("Activity", back_populates="department")
