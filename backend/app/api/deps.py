from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.department import DepartmentRepository
from app.repositories.team import TeamRepository
from app.repositories.session import SessionRepository
from app.repositories.attendance import AttendanceRepository
from app.services.user import UserService
from app.services.auth import AuthService
from app.services.organization import OrganizationService
from app.services.department import DepartmentService
from app.services.team import TeamService
from app.services.session import SessionService
from app.services.attendance import AttendanceService
from app.services.ai_verification import AIVerificationService
from app.services.analytics import AnalyticsService
from app.services.report import ReportService
from app.services.notification import NotificationService

# Reusable security scheme for SPA applications utilizing Bearer Authentication tokens
reusable_oauth2 = HTTPBearer(auto_error=True)

# 1. Database and Repository dependency providers
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency injection provider for UserRepository."""
    return UserRepository(db)

def get_organization_repository(db: Session = Depends(get_db)) -> OrganizationRepository:
    """Dependency injection provider for OrganizationRepository."""
    return OrganizationRepository(db)

def get_department_repository(db: Session = Depends(get_db)) -> DepartmentRepository:
    """Dependency injection provider for DepartmentRepository."""
    return DepartmentRepository(db)

def get_team_repository(db: Session = Depends(get_db)) -> TeamRepository:
    """Dependency injection provider for TeamRepository."""
    return TeamRepository(db)

def get_session_repository(db: Session = Depends(get_db)) -> SessionRepository:
    """Dependency injection provider for SessionRepository."""
    return SessionRepository(db)

def get_attendance_repository(db: Session = Depends(get_db)) -> AttendanceRepository:
    """Dependency injection provider for AttendanceRepository."""
    return AttendanceRepository(db)

# 2. Service dependency providers
def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
    org_repo: OrganizationRepository = Depends(get_organization_repository),
    dept_repo: DepartmentRepository = Depends(get_department_repository),
    team_repo: TeamRepository = Depends(get_team_repository)
) -> UserService:
    """Dependency injection provider for UserService."""
    return UserService(user_repo, org_repo, dept_repo, team_repo)

def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    """Dependency injection provider for AuthService."""
    return AuthService(user_repo)

def get_organization_service(org_repo: OrganizationRepository = Depends(get_organization_repository)) -> OrganizationService:
    """Dependency injection provider for OrganizationService."""
    return OrganizationService(org_repo)

def get_department_service(
    dept_repo: DepartmentRepository = Depends(get_department_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    org_repo: OrganizationRepository = Depends(get_organization_repository)
) -> DepartmentService:
    """Dependency injection provider for DepartmentService."""
    return DepartmentService(dept_repo, user_repo, org_repo)

def get_team_service(
    team_repo: TeamRepository = Depends(get_team_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    dept_repo: DepartmentRepository = Depends(get_department_repository)
) -> TeamService:
    """Dependency injection provider for TeamService."""
    return TeamService(team_repo, user_repo, dept_repo)

def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    """Dependency injection provider for SessionService."""
    return SessionService(db)

def get_attendance_service(db: Session = Depends(get_db)) -> AttendanceService:
    """Dependency injection provider for AttendanceService."""
    return AttendanceService(db)

def get_ai_verification_service(db: Session = Depends(get_db)) -> AIVerificationService:
    """Dependency injection provider for AIVerificationService."""
    return AIVerificationService(db)

def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency injection provider for AnalyticsService."""
    return AnalyticsService(db)

def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    """Dependency injection provider for ReportService."""
    return ReportService(db)

def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    """Dependency injection provider for NotificationService."""
    return NotificationService(db)

# 3. Authentication guard dependencies
def get_current_user(
    token_creds: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """
    FastAPI dependency to extract JWT access token from headers, decode it,
    validate token signature, check expiration, and retrieve the authenticated user.
    """
    token = token_creds.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid: subject missing",
        )
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid: subject must be an integer ID",
        )
        
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
        
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency ensuring the extracted user has an active account.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    return current_user

class RoleChecker:
    """
    Dependency to check if the current active user has one of the allowed roles.
    """
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: Insufficient permissions to access this resource."
            )
        return current_user

# Predefined role guard dependencies
require_system_admin = RoleChecker([UserRole.SystemAdmin])
require_org_admin = RoleChecker([UserRole.SystemAdmin, UserRole.OrgAdmin])
require_coordinator = RoleChecker([UserRole.SystemAdmin, UserRole.OrgAdmin, UserRole.Coordinator])
require_faculty_or_above = RoleChecker([UserRole.SystemAdmin, UserRole.OrgAdmin, UserRole.Coordinator, UserRole.Faculty])
require_auditor_or_above = RoleChecker([UserRole.SystemAdmin, UserRole.OrgAdmin, UserRole.Coordinator, UserRole.Faculty, UserRole.Auditor])
require_any_authenticated = RoleChecker([
    UserRole.SystemAdmin, UserRole.OrgAdmin, UserRole.Coordinator,
    UserRole.Faculty, UserRole.Student, UserRole.Auditor, UserRole.Member
])

