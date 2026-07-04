from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.services.user_repository import user_repo
from app.models.user import User

# Reusable security scheme for SPA applications utilizing Bearer Authentication tokens
reusable_oauth2 = HTTPBearer(auto_error=True)

def get_current_user(token_creds: HTTPAuthorizationCredentials = Depends(reusable_oauth2)) -> User:
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
        
    user = user_repo.get_by_id(user_id)
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
