from fastapi import APIRouter, Depends
from app.schemas.auth import LoginRequest, TokenResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.user import UserResponse
from app.api.deps import get_current_active_user, get_auth_service
from app.services.auth import AuthService
from app.models.user import User

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    """
    Verify user credentials and return a JWT access token along with user information.
    """
    res = auth_service.login(login_data.email, login_data.password)
    return res

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """
    Retrieve details of the currently authenticated active user.
    """
    return current_user

@router.post("/forgot-password")
def forgot_password(request_data: ForgotPasswordRequest, auth_service: AuthService = Depends(get_auth_service)):
    """
    Initiate password recovery flow. Generates a temporary reset token.
    For local development and testing, the token is logged to stdout and returned in the API response.
    """
    res = auth_service.initiate_password_reset(request_data.email)
    return res

@router.post("/reset-password")
def reset_password(request_data: ResetPasswordRequest, auth_service: AuthService = Depends(get_auth_service)):
    """
    Reset user password using a valid, unexpired reset token.
    """
    auth_service.reset_password(request_data.token, request_data.new_password)
    return {
        "message": "Password has been successfully updated."
    }
