import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum, ForeignKey, Date, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserRole(str, enum.Enum):
    SystemAdmin = "SystemAdmin"
    OrgAdmin = "OrgAdmin"
    Coordinator = "Coordinator"
    Faculty = "Faculty"
    Student = "Student"
    Auditor = "Auditor"
    Member = "Member"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.Member)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Extended Member Profile Columns
    profile_photo = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    gender = Column(String(20), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    emergency_contact = Column(String(255), nullable=True)
    joining_date = Column(Date, nullable=True)
    status = Column(String(50), nullable=False, default="Active")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="users")
    department = relationship("Department", back_populates="users", foreign_keys=[department_id])
    team = relationship("Team", back_populates="users", foreign_keys=[team_id])
    attendances = relationship("Attendance", back_populates="member", cascade="all, delete-orphan")
    assigned_activities = relationship("Activity", back_populates="assigned_to", foreign_keys="[Activity.assigned_to_id]")
    created_activities = relationship("Activity", back_populates="assigned_by", foreign_keys="[Activity.assigned_by_id]")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="generated_by")
    audit_logs = relationship("AuditLog", back_populates="actor")
    sessions = relationship("Session", secondary="session_members", back_populates="assigned_members")

