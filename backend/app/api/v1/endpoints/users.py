from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import (
    get_current_active_user, get_user_service,
    require_org_admin, require_any_authenticated
)
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.response import APIResponse
from app.services.user import UserService
from app.core.domain_exceptions import PermissionDeniedError, ObjectNotFoundError

router = APIRouter()

@router.get("/", response_model=APIResponse[List[UserResponse]])
def list_users(
    organization_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    team_id: Optional[int] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Search term for name/email/phone"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_any_authenticated),
    user_service: UserService = Depends(get_user_service)
):
    """
    List user directory with pagination, search, and scoping.
    Non-SystemAdmin users are restricted to listing users within their own organization.
    """
    if current_user.role != UserRole.SystemAdmin:
        if organization_id is not None and organization_id != current_user.organization_id:
            raise PermissionDeniedError("Permission denied: You cannot view members of another organization.")
        organization_id = current_user.organization_id

        # Coordinators are further scoped to their own department/team
        if current_user.role == UserRole.Coordinator:
            if department_id is not None and department_id != current_user.department_id:
                raise PermissionDeniedError("Permission denied: You can only query members within your department.")
            if team_id is not None and team_id != current_user.team_id:
                raise PermissionDeniedError("Permission denied: You can only query members within your team.")
            
            department_id = current_user.department_id
            team_id = current_user.team_id

    users = user_service.get_users_list(
        organization_id=organization_id,
        department_id=department_id,
        team_id=team_id,
        role=role,
        status=status,
        search_query=q,
        skip=skip,
        limit=limit
    )
    total = user_service.get_users_count(
        organization_id=organization_id,
        department_id=department_id,
        team_id=team_id,
        role=role,
        status=status,
        search_query=q
    )

    return APIResponse(
        success=True,
        data=users,
        message=f"Retrieved {len(users)} users (Total: {total})."
    )

@router.get("/{id}", response_model=APIResponse[UserResponse])
def get_user(
    id: int,
    current_user: User = Depends(require_any_authenticated),
    user_service: UserService = Depends(get_user_service)
):
    """
    Fetch a single user profile.
    """
    user = user_service.get_user_by_id(id)
    if not user:
        raise ObjectNotFoundError(f"User with ID {id} not found.")

    if current_user.role != UserRole.SystemAdmin and user.organization_id != current_user.organization_id:
        raise PermissionDeniedError("Permission denied: You cannot view members of another organization.")

    return APIResponse(
        success=True,
        data=user,
        message="User profile retrieved successfully."
    )

@router.post("/", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Create a new user/member.
    OrgAdmin can only create users belonging to their own organization_id.
    """
    if current_user.role != UserRole.SystemAdmin:
        if user_in.organization_id != current_user.organization_id:
            raise PermissionDeniedError("Permission denied: You can only create members for your own organization.")

    new_user = user_service.create_user(db, user_in, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=new_user,
        message="User successfully registered."
    )

@router.put("/{id}", response_model=APIResponse[UserResponse])
def update_user(
    id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user profile.
    SystemAdmin: Full access.
    OrgAdmin: Can update users within their own organization.
    Coordinator: Can update members in their own team.
    Any user: Can update their own profile (phone, password, gender, emergency_contact, profile_photo) but cannot modify roles, statuses, active state, organization, department, or team.
    """
    user = user_service.get_user_by_id(id)
    if not user:
        raise ObjectNotFoundError(f"User with ID {id} not found.")

    # Determine access level
    is_self = current_user.id == id
    is_admin = current_user.role in [UserRole.SystemAdmin, UserRole.OrgAdmin]
    
    if not is_self and not is_admin:
        raise PermissionDeniedError("Permission denied: You can only update your own profile or manage as Admin.")

    if current_user.role != UserRole.SystemAdmin and user.organization_id != current_user.organization_id:
        raise PermissionDeniedError("Permission denied: Target user belongs to another organization.")

    if is_self and not is_admin:
        # Enforce restricted updates for self
        restricted_keys = ["role", "is_active", "status", "organization_id", "department_id", "team_id"]
        update_data = user_in.model_dump(exclude_unset=True)
        for key in restricted_keys:
            if key in update_data:
                raise PermissionDeniedError(f"Permission denied: You cannot modify your own '{key}' field.")

    updated_user = user_service.update_user(db, id, user_in, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=updated_user,
        message="User details successfully updated."
    )

@router.delete("/{id}", response_model=APIResponse[UserResponse])
def deactivate_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Deactivate a user account (soft delete).
    """
    user = user_service.get_user_by_id(id)
    if not user:
        raise ObjectNotFoundError(f"User with ID {id} not found.")

    if current_user.role != UserRole.SystemAdmin and user.organization_id != current_user.organization_id:
        raise PermissionDeniedError("Permission denied: Target user belongs to another organization.")

    deactivated = user_service.deactivate_user(db, id, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=deactivated,
        message="User account successfully deactivated."
    )

@router.post("/{id}/activate", response_model=APIResponse[UserResponse])
def activate_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Activate a user account.
    """
    user = user_service.get_user_by_id(id)
    if not user:
        raise ObjectNotFoundError(f"User with ID {id} not found.")

    if current_user.role != UserRole.SystemAdmin and user.organization_id != current_user.organization_id:
        raise PermissionDeniedError("Permission denied: Target user belongs to another organization.")

    activated = user_service.activate_user(db, id, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=activated,
        message="User account successfully activated."
    )
