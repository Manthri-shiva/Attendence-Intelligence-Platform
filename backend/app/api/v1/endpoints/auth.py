from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.services.user_repository import user_repo
from app.schemas.auth import LoginRequest, TokenResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.user import UserResponse
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest):
    """
    Verify user credentials and return a JWT access token along with user information.
    """
    user = user_repo.get_by_email(login_data.email)
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )
        
    access_token = create_access_token(
        subject=user.id,
        role=user.role.value
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """
    Retrieve details of the currently authenticated active user.
    """
    return current_user

@router.post("/forgot-password")
def forgot_password(request_data: ForgotPasswordRequest):
    """
    Initiate password recovery flow. Generates a temporary reset token.
    For local development and testing, the token is logged to stdout and returned in the API response.
    """
    user = user_repo.get_by_email(request_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account associated with this email address"
        )
        
    reset_token = create_access_token(
        subject=user.email,
        role="PasswordReset",
        expires_delta=timedelta(minutes=15)
    )
    
    # In production, this would trigger an email delivery service.
    print(f"[MAIL MOCK] Password reset request for {user.email}. Token: {reset_token}")
    
    return {
        "message": "Password reset instructions have been sent to your email address.",
        "token": reset_token
    }

@router.post("/reset-password")
def reset_password(request_data: ResetPasswordRequest):
    """
    Reset user password using a valid, unexpired reset token.
    """
    payload = decode_access_token(request_data.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The password reset link is invalid or has expired."
        )
        
    email = payload.get("sub")
    role = payload.get("role")
    if not email or role != "PasswordReset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token payload credentials."
        )
        
    new_hashed_password = get_password_hash(request_data.new_password)
    updated = user_repo.update_password(email, new_hashed_password)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account could not be found."
        )
        
    return {
        "message": "Password has been successfully updated."
    }
