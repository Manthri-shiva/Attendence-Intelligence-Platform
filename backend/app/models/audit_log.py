from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False) # e.g. "Create", "Update", "Delete", "Login"
    module = Column(String(100), nullable=False) # e.g. "Auth", "Session", "Attendance"
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    device = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)

    # Relationships
    actor = relationship("User", back_populates="audit_logs")
