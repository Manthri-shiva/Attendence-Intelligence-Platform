from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import (
    get_current_active_user, get_department_service,
    require_org_admin, require_any_authenticated
)
from app.models.user import User, UserRole
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.schemas.response import APIResponse
from app.services.department import DepartmentService
from app.core.domain_exceptions import PermissionDeniedError, ObjectNotFoundError

router = APIRouter()

@router.get("/", response_model=APIResponse[List[DepartmentResponse]])
def list_departments(
    organization_id: Optional[int] = Query(None, description="Filter by Organization ID"),
    q: Optional[str] = Query(None, description="Search term for department name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_any_authenticated),
    dept_service: DepartmentService = Depends(get_department_service)
):
    """
    List departments with pagination, search queries, and organization scoping.
    Non-SystemAdmin users can only retrieve departments inside their assigned organization.
    """
    # Enforce tenant scoping
    if current_user.role != UserRole.SystemAdmin:
        if organization_id is not None and organization_id != current_user.organization_id:
            raise PermissionDeniedError("Permission denied: You cannot query departments of other organizations.")
        organization_id = current_user.organization_id

    if q:
        depts = dept_service.search_depts(q, organization_id=organization_id, skip=skip, limit=limit)
        total = dept_service.count_depts(q, organization_id=organization_id)
    else:
        if organization_id is not None:
            depts = dept_service.get_depts_by_org(organization_id, skip=skip, limit=limit)
            total = dept_service.count_depts(organization_id=organization_id)
        else:
            depts = dept_service.get_all_depts(skip=skip, limit=limit)
            total = dept_service.count_depts()

    return APIResponse(
        success=True,
        data=depts,
        message=f"Retrieved {len(depts)} departments (Total: {total})."
    )

@router.get("/{id}", response_model=APIResponse[DepartmentResponse])
def get_department(
    id: int,
    current_user: User = Depends(require_any_authenticated),
    dept_service: DepartmentService = Depends(get_department_service)
):
    """
    Retrieve single department details. Enforces organization scope checks.
    """
    dept = dept_service.get_dept_by_id(id)
    if not dept:
        raise ObjectNotFoundError(f"Department with ID {id} not found.")

    if current_user.role != UserRole.SystemAdmin and dept.organization_id != current_user.organization_id:
        raise PermissionDeniedError("Permission denied: You cannot view departments of other organizations.")

    return APIResponse(
        success=True,
        data=dept,
        message="Department details retrieved successfully."
    )

@router.post("/", response_model=APIResponse[DepartmentResponse], status_code=status.HTTP_201_CREATED)
def create_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    dept_service: DepartmentService = Depends(get_department_service)
):
    """
    Create a new department.
    OrgAdmin can only register departments inside their own organization_id.
    """
    if current_user.role != UserRole.SystemAdmin and dept_in.organization_id != current_user.organization_id:
        raise PermissionDeniedError("Permission denied: You can only create departments for your own organization.")

    new_dept = dept_service.create_dept(db, dept_in, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=new_dept,
        message="Department successfully registered."
    )

@router.put("/{id}", response_model=APIResponse[DepartmentResponse])
def update_department(
    id: int,
    dept_in: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    dept_service: DepartmentService = Depends(get_department_service)
):
    """
    Update department configurations.
    OrgAdmin can only update departments inside their own organization_id.
    """
    dept = dept_service.get_dept_by_id(id)
    if not dept:
        raise ObjectNotFoundError(f"Department with ID {id} not found.")

    if current_user.role != UserRole.SystemAdmin:
        if dept.organization_id != current_user.organization_id:
            raise PermissionDeniedError("Permission denied: You cannot update departments of other organizations.")
        if dept_in.organization_id is not None and dept_in.organization_id != current_user.organization_id:
            raise PermissionDeniedError("Permission denied: You cannot reassign department to another organization.")

    updated_dept = dept_service.update_dept(db, id, dept_in, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=updated_dept,
        message="Department successfully updated."
    )

@router.delete("/{id}", response_model=APIResponse[DepartmentResponse])
def delete_department(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    dept_service: DepartmentService = Depends(get_department_service)
):
    """
    Soft-delete/Deactivate department.
    OrgAdmin can only deactivate departments inside their own organization_id.
    """
    dept = dept_service.get_dept_by_id(id)
    if not dept:
        raise ObjectNotFoundError(f"Department with ID {id} not found.")

    if current_user.role != UserRole.SystemAdmin and dept.organization_id != current_user.organization_id:
        raise PermissionDeniedError("Permission denied: You cannot delete departments of other organizations.")

    deleted_dept = dept_service.delete_dept(db, id, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=deleted_dept,
        message="Department status successfully updated to Inactive."
    )
