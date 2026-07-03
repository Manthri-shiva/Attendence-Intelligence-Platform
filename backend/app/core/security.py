from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Hashing context using bcrypt algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash of a plain text password."""
    return pwd_context.hash(password)

def create_access_token(
    subject: Union[str, Any], 
    role: str,
    expires_delta: Union[timedelta, None] = None
) -> str:
    """
    Generate a JSON Web Token (JWT) for authenticated sessions.
    
    Args:
        subject: Unique identifier (usually user id or email) for the token owner.
        role: User privilege role (SystemAdmin, OrgAdmin, Coordinator, Member, Auditor).
        expires_delta: Custom token duration. Defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire, 
        "sub": str(subject),
        "role": role
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> Union[dict, None]:
    """
    Decode and validate a JWT access token.
    
    Returns:
        Dictionary payload if valid, otherwise None.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.JWTError:
        return None
