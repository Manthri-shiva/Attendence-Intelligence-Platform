from datetime import timedelta
from typing import Dict, Any
from app.repositories.user import UserRepository
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.domain_exceptions import (
    UserNotFoundError, InvalidCredentialsError, InactiveUserError, TokenExpiredOrInvalidError
)

class AuthService:
    """
    Service layer orchestrating authentication, login, and password recovery rules.
    """
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user credentials and return a signed JWT token with user object.
        """
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Incorrect email or password")
            
        if not user.is_active:
            raise InactiveUserError("User account is inactive")
            
        access_token = create_access_token(
            subject=user.id,
            role=user.role.value
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }

    def initiate_password_reset(self, email: str) -> Dict[str, str]:
        """
        Initiate password recovery. Generates a short-lived reset token.
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundError("No account associated with this email address")
            
        reset_token = create_access_token(
            subject=user.email,
            role="PasswordReset",
            expires_delta=timedelta(minutes=15)
        )
        
        # Log to stdout as per local mail mock requirement
        print(f"[MAIL MOCK] Password reset request for {user.email}. Token: {reset_token}")
        
        return {
            "message": "Password reset instructions have been sent to your email address.",
            "token": reset_token
        }

    def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset account password using a validated reset token.
        """
        payload = decode_access_token(token)
        if not payload:
            raise TokenExpiredOrInvalidError("The password reset link is invalid or has expired.")
            
        email = payload.get("sub")
        role = payload.get("role")
        if not email or role != "PasswordReset":
            raise TokenExpiredOrInvalidError("Invalid token payload credentials.")
            
        user = self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundError("User account could not be found.")
            
        hashed_pwd = get_password_hash(new_password)
        self.user_repo.update(user, {"hashed_password": hashed_pwd})
