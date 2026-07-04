from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(String(100), nullable=False) # e.g. "Attendance", "Activity"
    format = Column(String(50), nullable=False) # e.g. "Excel", "PDF"
    generated_by_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    generated_by = relationship("User", back_populates="reports")
