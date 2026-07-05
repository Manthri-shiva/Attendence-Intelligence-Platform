from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import (
    get_current_active_user, get_organization_service,
    require_system_admin, require_any_authenticated
)
from app.models.user import User, UserRole
from app.schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationResponse
from app.schemas.response import APIResponse
from app.services.organization import OrganizationService
from app.core.domain_exceptions import PermissionDeniedError

router = APIRouter()

@router.get("/", response_model=APIResponse[List[OrganizationResponse]])
def list_organizations(
    q: Optional[str] = Query(None, description="Search term for name/email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_any_authenticated),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    List organizations with pagination and search queries.
    SystemAdmin gets all. Other roles are restricted to viewing only their assigned organization.
    """
    if current_user.role == UserRole.SystemAdmin:
        if q:
            orgs = org_service.search_orgs(q, skip=skip, limit=limit)
            total = org_service.count_orgs(q)
        else:
            orgs = org_service.get_all_orgs(skip=skip, limit=limit)
            total = org_service.count_orgs()
    else:
        # Non-system admins can only view their own organization
        if not current_user.organization_id:
            orgs = []
            total = 0
        else:
            org = org_service.get_org_by_id(current_user.organization_id)
            orgs = [org] if org else []
            total = len(orgs)

    return APIResponse(
        success=True,
        data=orgs,
        message=f"Retrieved {len(orgs)} organizations (Total: {total})."
    )

@router.get("/{id}", response_model=APIResponse[OrganizationResponse])
def get_organization(
    id: int,
    current_user: User = Depends(require_any_authenticated),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Fetch a single organization profile. Enforces tenant scope boundaries for non-system admins.
    """
    if current_user.role != UserRole.SystemAdmin and current_user.organization_id != id:
        raise PermissionDeniedError("You do not have permission to view this organization profile.")

    org = org_service.get_org_by_id(id)
    if not org:
        raise PermissionDeniedError("Organization not found.")

    return APIResponse(
        success=True,
        data=org,
        message="Organization profile retrieved successfully."
    )

@router.post("/", response_model=APIResponse[OrganizationResponse], status_code=status.HTTP_201_CREATED)
def create_organization(
    org_in: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_system_admin),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Create a new organization. Restricted to Super Admin (SystemAdmin).
    """
    new_org = org_service.create_org(db, org_in, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=new_org,
        message="Organization successfully created."
    )

@router.put("/{id}", response_model=APIResponse[OrganizationResponse])
def update_organization(
    id: int,
    org_in: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_system_admin),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Update an organization's configuration details. Restricted to Super Admin (SystemAdmin).
    """
    updated_org = org_service.update_org(db, id, org_in, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=updated_org,
        message="Organization details successfully updated."
    )

@router.delete("/{id}", response_model=APIResponse[OrganizationResponse])
def delete_organization(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_system_admin),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Soft-delete/Deactivate an organization. Restricted to Super Admin (SystemAdmin).
    """
    deleted_org = org_service.delete_org(db, id, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=deleted_org,
        message="Organization status successfully set to Inactive."
    )
