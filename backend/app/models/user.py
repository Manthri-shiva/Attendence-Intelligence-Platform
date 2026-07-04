import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum
from app.core.database import Base

class UserRole(str, enum.Enum):
    SystemAdmin = "SystemAdmin"
    OrgAdmin = "OrgAdmin"
    Coordinator = "Coordinator"
    Member = "Member"
    Auditor = "Auditor"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.Member)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
