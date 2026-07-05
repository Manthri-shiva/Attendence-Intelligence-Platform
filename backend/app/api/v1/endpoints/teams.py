from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import (
    get_current_active_user, get_team_service, get_department_service,
    require_org_admin, require_any_authenticated
)
from app.models.user import User, UserRole
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse
from app.schemas.response import APIResponse
from app.services.team import TeamService
from app.services.department import DepartmentService
from app.core.domain_exceptions import PermissionDeniedError, ObjectNotFoundError

router = APIRouter()

@router.get("/", response_model=APIResponse[List[TeamResponse]])
def list_teams(
    department_id: Optional[int] = Query(None, description="Filter by Department ID"),
    q: Optional[str] = Query(None, description="Search term for team name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_any_authenticated),
    team_service: TeamService = Depends(get_team_service),
    dept_service: DepartmentService = Depends(get_department_service)
):
    """
    List teams with pagination, search, and department scoping.
    Non-SystemAdmin users can only view teams belonging to departments within their assigned organization.
    """
    # Enforce tenant department scoping
    if current_user.role != UserRole.SystemAdmin:
        if department_id is not None:
            dept = dept_service.get_dept_by_id(department_id)
            if not dept or dept.organization_id != current_user.organization_id:
                raise PermissionDeniedError("Permission denied: You cannot query teams of other organizations.")
        else:
            # If no department_id is specified for a non-system admin, 
            # we query all departments in their organization to find their teams.
            depts = dept_service.get_depts_by_org(current_user.organization_id, limit=1000)
            dept_ids = [d.id for d in depts]
            
            # Query teams belonging to those department IDs
            q_teams = team_service.team_repo.db.query(team_service.team_repo.model)
            if q:
                q_teams = q_teams.filter(team_service.team_repo.model.name.ilike(f"%{q}%"))
            q_teams = q_teams.filter(team_service.team_repo.model.department_id.in_(dept_ids))
            total = q_teams.count()
            teams = q_teams.offset(skip).limit(limit).all()
            
            return APIResponse(
                success=True,
                data=teams,
                message=f"Retrieved {len(teams)} teams (Total: {total})."
            )

    # SystemAdmin flow
    if q:
        teams = team_service.search_teams(q, department_id=department_id, skip=skip, limit=limit)
        total = team_service.count_teams(q, department_id=department_id)
    else:
        if department_id is not None:
            teams = team_service.get_teams_by_dept(department_id, skip=skip, limit=limit)
            total = team_service.count_teams(department_id=department_id)
        else:
            teams = team_service.get_all_teams(skip=skip, limit=limit)
            total = team_service.count_teams()

    return APIResponse(
        success=True,
        data=teams,
        message=f"Retrieved {len(teams)} teams (Total: {total})."
    )

@router.get("/{id}", response_model=APIResponse[TeamResponse])
def get_team(
    id: int,
    current_user: User = Depends(require_any_authenticated),
    team_service: TeamService = Depends(get_team_service)
):
    """
    Retrieve single team details. Enforces tenant scope checks.
    """
    team = team_service.get_team_by_id(id)
    if not team:
        raise ObjectNotFoundError(f"Team with ID {id} not found.")

    if current_user.role != UserRole.SystemAdmin:
        if team.department.organization_id != current_user.organization_id:
            raise PermissionDeniedError("Permission denied: You cannot view teams of other organizations.")

    return APIResponse(
        success=True,
        data=team,
        message="Team details retrieved successfully."
    )

@router.post("/", response_model=APIResponse[TeamResponse], status_code=status.HTTP_201_CREATED)
def create_team(
    team_in: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    team_service: TeamService = Depends(get_team_service),
    dept_service: DepartmentService = Depends(get_department_service)
):
    """
    Create a new team.
    OrgAdmin can only register teams inside departments belonging to their organization.
    """
    dept = dept_service.get_dept_by_id(team_in.department_id)
    if not dept:
        raise ObjectNotFoundError(f"Department with ID {team_in.department_id} not found.")

    if current_user.role != UserRole.SystemAdmin and dept.organization_id != current_user.organization_id:
        raise PermissionDeniedError("Permission denied: You cannot create a team for a department in another organization.")

    new_team = team_service.create_team(db, team_in, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=new_team,
        message="Team successfully registered."
    )

@router.put("/{id}", response_model=APIResponse[TeamResponse])
def update_team(
    id: int,
    team_in: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    team_service: TeamService = Depends(get_team_service),
    dept_service: DepartmentService = Depends(get_department_service)
):
    """
    Update team details.
    OrgAdmin can only update teams belonging to departments within their organization.
    """
    team = team_service.get_team_by_id(id)
    if not team:
        raise ObjectNotFoundError(f"Team with ID {id} not found.")

    if current_user.role != UserRole.SystemAdmin:
        if team.department.organization_id != current_user.organization_id:
            raise PermissionDeniedError("Permission denied: You cannot update teams of other organizations.")
        if team_in.department_id is not None:
            target_dept = dept_service.get_dept_by_id(team_in.department_id)
            if not target_dept or target_dept.organization_id != current_user.organization_id:
                raise PermissionDeniedError("Permission denied: Target department must belong to your organization.")

    updated_team = team_service.update_team(db, id, team_in, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=updated_team,
        message="Team successfully updated."
    )

@router.delete("/{id}", response_model=APIResponse[TeamResponse])
def delete_team(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    team_service: TeamService = Depends(get_team_service)
):
    """
    Soft-delete/Deactivate team.
    OrgAdmin can only deactivate teams belonging to their organization.
    """
    team = team_service.get_team_by_id(id)
    if not team:
        raise ObjectNotFoundError(f"Team with ID {id} not found.")

    if current_user.role != UserRole.SystemAdmin and team.department.organization_id != current_user.organization_id:
        raise PermissionDeniedError("Permission denied: You cannot delete teams of other organizations.")

    deleted_team = team_service.delete_team(db, id, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=deleted_team,
        message="Team status successfully updated to Inactive."
    )
