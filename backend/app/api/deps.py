from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.user import UserService
from app.services.auth import AuthService

# Reusable security scheme for SPA applications utilizing Bearer Authentication tokens
reusable_oauth2 = HTTPBearer(auto_error=True)

# 1. Database and Repository dependency providers
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency injection provider for UserRepository."""
    return UserRepository(db)

# 2. Service dependency providers
def get_user_service(user_repo: UserRepository = Depends(get_user_repository)) -> UserService:
    """Dependency injection provider for UserService."""
    return UserService(user_repo)

def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    """Dependency injection provider for AuthService."""
    return AuthService(user_repo)

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
