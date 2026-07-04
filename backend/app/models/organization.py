from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    logo = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(100), nullable=True, default="UTC")
    address = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="Active")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization")
    sessions = relationship("Session", back_populates="organization")
