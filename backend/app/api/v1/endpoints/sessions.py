from fastapi import APIRouter, Depends, Query, Header, status, Request
from typing import Optional, List
from datetime import date, datetime
from app.models.user import User, UserRole
from app.api.deps import (
    get_current_active_user, get_session_service, get_attendance_service,
    get_ai_verification_service, require_coordinator, require_org_admin,
    require_any_authenticated
)
from app.services.session import SessionService
from app.services.attendance import AttendanceService
from app.services.ai_verification import AIVerificationService
from app.schemas.response import APIResponse
from app.schemas.session import (
    SessionCreate, SessionUpdate, SessionResponse, SessionAssignMembers,
    CheckInRequest, CheckOutRequest
)
from app.schemas.attendance import AttendanceResponse, CheckInResponse
from app.models.attendance import Attendance
from app.core.domain_exceptions import PermissionDeniedError, ObjectNotFoundError
from app.services.audit_log import AuditLogService

router = APIRouter()

@router.post("/", response_model=APIResponse[SessionResponse], status_code=status.HTTP_201_CREATED)
def create_session(
    schema: SessionCreate,
    current_user: User = Depends(require_coordinator),
    service: SessionService = Depends(get_session_service)
):
    """
    Schedule/register a new session.
    Coordinators and Org Admins are bound to their respective organization tenant.
    """
    # Enforce tenant scoping
    if current_user.role != UserRole.SystemAdmin:
        schema.organization_id = current_user.organization_id
        if current_user.role == UserRole.Coordinator and current_user.department_id:
            schema.department_id = current_user.department_id

    session = service.create_session(schema, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=SessionResponse.model_validate(session),
        message="Session scheduled successfully."
    )

@router.get("/", response_model=APIResponse[List[SessionResponse]])
def get_sessions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    q: Optional[str] = Query(default=None),
    organization_id: Optional[int] = Query(default=None),
    department_id: Optional[int] = Query(default=None),
    coordinator_id: Optional[int] = Query(default=None),
    date_val: Optional[date] = Query(default=None, alias="date"),
    status_val: Optional[str] = Query(default=None, alias="status"),
    current_user: User = Depends(require_any_authenticated),
    service: SessionService = Depends(get_session_service)
):
    """
    Retrieve sessions with pagination, text-searches, and filters.
    Automatically scopes queries to the user's organization tenant.
    """
    # Enforce tenant scoping boundaries
    if current_user.role != UserRole.SystemAdmin:
        organization_id = current_user.organization_id

    sessions = service.get_sessions(
        skip=skip,
        limit=limit,
        q=q,
        organization_id=organization_id,
        department_id=department_id,
        coordinator_id=coordinator_id,
        filter_date=date_val,
        status=status_val
    )
    total = service.count_sessions(
        q=q,
        organization_id=organization_id,
        department_id=department_id,
        coordinator_id=coordinator_id,
        filter_date=date_val,
        status=status_val
    )

    data_payload = [SessionResponse.model_validate(s) for s in sessions]
    return APIResponse(
        success=True,
        data=data_payload,
        message=f"Sessions retrieved successfully. Total: {total}"
    )

# --- Attendance Evidence Viewer API ---

@router.get("/attendances/all", response_model=APIResponse[List[AttendanceResponse]])
def get_all_attendances(
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = None,
    organization_id: Optional[int] = None,
    department_id: Optional[int] = None,
    team_id: Optional[int] = None,
    member_id: Optional[int] = None,
    session_id: Optional[int] = None,
    status: Optional[str] = None,
    date: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    service: AttendanceService = Depends(get_attendance_service)
):
    """
    Get all attendance records with advanced filtering, search, and RBAC enforcement.
    """
    query = service.db.query(Attendance).join(User, Attendance.member_id == User.id).join(Session, Attendance.session_id == Session.id)
    
    # Apply Role-based access filters
    if current_user.role in [UserRole.Member, UserRole.Student]:
        query = query.filter(Attendance.member_id == current_user.id)
    elif current_user.role == UserRole.Coordinator:
        # Coordinator manages sessions where coordinator_id is their user id
        query = query.filter(Session.coordinator_id == current_user.id)
    elif current_user.role == UserRole.OrgAdmin:
        # OrgAdmin can see their organization's sessions
        query = query.filter(Session.organization_id == current_user.organization_id)
    # SystemAdmin and Auditor have global visibility (no extra filter)
    
    # Apply filters
    if organization_id:
        query = query.filter(Session.organization_id == organization_id)
    if department_id:
        query = query.filter(Session.department_id == department_id)
    if team_id:
        query = query.filter(User.team_id == team_id)
    if member_id:
        query = query.filter(Attendance.member_id == member_id)
    if session_id:
        query = query.filter(Attendance.session_id == session_id)
    if status:
        query = query.filter(Attendance.status == status)
    if date:
        query = query.filter(Session.date == date)
        
    # Apply search (Name, Email, Session name)
    if q:
        search_filter = f"%{q}%"
        query = query.filter(
            (User.full_name.ilike(search_filter)) |
            (User.email.ilike(search_filter)) |
            (Session.name.ilike(search_filter))
        )
        
    total = query.count()
    records = query.order_by(Attendance.created_at.desc()).offset(skip).limit(limit).all()
    
    payload = [AttendanceResponse.model_validate(r) for r in records]
    return APIResponse(
        success=True,
        data=payload,
        message=f"Retrieved {len(payload)} attendance records. Total: {total}"
    )

@router.get("/attendances/{attendance_id}/evidence")
def get_attendance_evidence(
    attendance_id: int,
    current_user: User = Depends(get_current_active_user),
    service: AttendanceService = Depends(get_attendance_service)
):
    """
    Fetch evidence details for a specific attendance record, verifying RBAC and logging access.
    """
    record = service.db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise ObjectNotFoundError(f"Attendance record {attendance_id} not found.")
        
    # RBAC check
    session = service.db.query(Session).filter(Session.id == record.session_id).first()
    
    is_allowed = False
    if current_user.role in [UserRole.SystemAdmin, UserRole.Auditor]:
        is_allowed = True
    elif current_user.role == UserRole.OrgAdmin:
        if session and session.organization_id == current_user.organization_id:
            is_allowed = True
    elif current_user.role == UserRole.Coordinator:
        if session and session.coordinator_id == current_user.id:
            is_allowed = True
    elif current_user.role in [UserRole.Member, UserRole.Student]:
        if record.member_id == current_user.id:
            is_allowed = True
            
    if not is_allowed:
        raise PermissionDeniedError("You do not have permission to view this evidence.")
        
    # Log Audit Event
    AuditLogService.log_event(
        db=service.db,
        actor_id=current_user.id,
        action="EvidenceViewed",
        module="Attendance_Evidence",
        new_value=f"User {current_user.id} viewed evidence for attendance {attendance_id} (Member: {record.member_id})"
    )
    
    # Return details
    return APIResponse(
        success=True,
        data={
            "attendance_id": record.id,
            "member_id": record.member_id,
            "member_name": record.member.full_name if record.member else "Unknown",
            "profile_photo": record.member.profile_photo if record.member else None,
            "selfie_image_path": record.selfie_image_path,
            "session_name": session.name if session else "Unknown",
            "check_in_time": record.check_in_time.isoformat() if record.check_in_time else None,
            "gps_latitude": record.gps_latitude,
            "gps_longitude": record.gps_longitude,
            "gps_accuracy": record.gps_accuracy,
            "verification_status": record.verification_status,
            "confidence_score": record.confidence_score,
            "liveness_score": record.liveness_score,
            "device_name": record.device_name,
            "browser_name": record.browser_name,
            "user_agent": record.user_agent,
            "ip_address": record.ip_address,
            "captured_at": record.captured_at.isoformat() if record.captured_at else None
        },
        message="Attendance evidence retrieved successfully."
    )

@router.get("/{id}", response_model=APIResponse[SessionResponse])
def get_session_by_id(
    id: int,
    current_user: User = Depends(require_any_authenticated),
    service: SessionService = Depends(get_session_service)
):
    """Retrieve detailed properties of a session by ID."""
    session = service.get_session(id)

    # Scoped check
    if current_user.role != UserRole.SystemAdmin and session.organization_id != current_user.organization_id:
        raise PermissionDeniedError("Access denied: Session belongs to another tenant.")

    return APIResponse(
        success=True,
        data=SessionResponse.model_validate(session),
        message="Session details retrieved."
    )

@router.put("/{id}", response_model=APIResponse[SessionResponse])
def update_session(
    id: int,
    schema: SessionUpdate,
    x_updated_at: Optional[str] = Header(None, alias="X-Updated-At"),
    current_user: User = Depends(require_coordinator),
    service: SessionService = Depends(get_session_service)
):
    """
    Modify details of a scheduled session.
    Guarded by optimistic concurrency checks using the X-Updated-At timestamp header.
    """
    session = service.get_session(id)

    # Tenant constraint check
    if current_user.role != UserRole.SystemAdmin and session.organization_id != current_user.organization_id:
        raise PermissionDeniedError("Access denied: Session belongs to another tenant.")

    # Parse concurrency verification timestamp
    check_updated_at = None
    if x_updated_at:
        try:
            check_updated_at = datetime.fromisoformat(x_updated_at.replace("Z", "+00:00"))
        except ValueError:
            pass

    updated = service.update_session(
        session_id=id,
        schema=schema,
        actor_id=current_user.id,
        check_updated_at=check_updated_at
    )
    return APIResponse(
        success=True,
        data=SessionResponse.model_validate(updated),
        message="Session parameters updated successfully."
    )

@router.delete("/{id}", response_model=APIResponse[None])
def delete_session(
    id: int,
    current_user: User = Depends(require_coordinator),
    service: SessionService = Depends(get_session_service)
):
    """Remove a scheduled session. Deletion is blocked once a session becomes Active."""
    session = service.get_session(id)

    if current_user.role != UserRole.SystemAdmin and session.organization_id != current_user.organization_id:
        raise PermissionDeniedError("Access denied: Session belongs to another tenant.")

    service.delete_session(id, actor_id=current_user.id)
    return APIResponse(
        success=True,
        message="Session deleted successfully."
    )

# --- Lifecycle State Transitions ---

@router.post("/{id}/publish", response_model=APIResponse[SessionResponse])
def publish_session(
    id: int,
    current_user: User = Depends(require_coordinator),
    service: SessionService = Depends(get_session_service)
):
    """Transition draft session status to Scheduled."""
    session = service.transition_state(id, "Scheduled", actor_id=current_user.id)
    return APIResponse(success=True, data=SessionResponse.model_validate(session), message="Session published/scheduled.")

@router.post("/{id}/start", response_model=APIResponse[SessionResponse])
def start_session(
    id: int,
    current_user: User = Depends(require_coordinator),
    service: SessionService = Depends(get_session_service)
):
    """Transition session status to Active. Initiates attendance window."""
    session = service.transition_state(id, "Active", actor_id=current_user.id)
    return APIResponse(success=True, data=SessionResponse.model_validate(session), message="Session is now active.")

@router.post("/{id}/pause", response_model=APIResponse[SessionResponse])
def pause_session(
    id: int,
    current_user: User = Depends(require_coordinator),
    service: SessionService = Depends(get_session_service)
):
    """Suspend attendance check-ins temporarily."""
    session = service.transition_state(id, "Paused", actor_id=current_user.id)
    return APIResponse(success=True, data=SessionResponse.model_validate(session), message="Session attendance paused.")

@router.post("/{id}/complete", response_model=APIResponse[SessionResponse])
def complete_session(
    id: int,
    current_user: User = Depends(require_coordinator),
    service: SessionService = Depends(get_session_service)
):
    """Transition session status to Completed."""
    session = service.transition_state(id, "Completed", actor_id=current_user.id)
    return APIResponse(success=True, data=SessionResponse.model_validate(session), message="Session marked as completed.")

@router.post("/{id}/cancel", response_model=APIResponse[SessionResponse])
def cancel_session(
    id: int,
    current_user: User = Depends(require_coordinator),
    service: SessionService = Depends(get_session_service)
):
    """Cancel a scheduled session."""
    session = service.transition_state(id, "Cancelled", actor_id=current_user.id)
    return APIResponse(success=True, data=SessionResponse.model_validate(session), message="Session cancelled.")

@router.post("/{id}/archive", response_model=APIResponse[SessionResponse])
def archive_session(
    id: int,
    current_user: User = Depends(require_coordinator),
    service: SessionService = Depends(get_session_service)
):
    """Archive a finished/cancelled session."""
    session = service.transition_state(id, "Archived", actor_id=current_user.id)
    return APIResponse(success=True, data=SessionResponse.model_validate(session), message="Session archived.")

# --- Participant Management ---

@router.post("/{id}/assign-members", response_model=APIResponse[SessionResponse])
def assign_members(
    id: int,
    schema: SessionAssignMembers,
    current_user: User = Depends(require_coordinator),
    service: SessionService = Depends(get_session_service)
):
    """Bulk assign participants to the session roster."""
    updated = service.assign_members(id, schema.user_ids, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=SessionResponse.model_validate(updated),
        message=f"Assigned {len(schema.user_ids)} members to the session."
    )

@router.post("/{id}/remove-members", response_model=APIResponse[SessionResponse])
def remove_members(
    id: int,
    schema: SessionAssignMembers,
    current_user: User = Depends(require_coordinator),
    service: SessionService = Depends(get_session_service)
):
    """Bulk remove participants from the session roster."""
    updated = service.remove_members(id, schema.user_ids, actor_id=current_user.id)
    return APIResponse(
        success=True,
        data=SessionResponse.model_validate(updated),
        message=f"Removed {len(schema.user_ids)} members from the session."
    )

# --- Attendance Check-in & Check-out ---

@router.post("/{id}/check-in", response_model=APIResponse[CheckInResponse])
def check_in(
    id: int,
    schema: CheckInRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    ai_service: AIVerificationService = Depends(get_ai_verification_service)
):
    """GPS + AI Face Recognition + Liveness verified check-in for the current active user."""
    user_agent = request.headers.get("user-agent")
    client_ip = request.client.host if request.client else None
    
    att = ai_service.verify_and_check_in(
        session_id=id,
        member_id=current_user.id,
        latitude=schema.latitude,
        longitude=schema.longitude,
        image_b64=schema.image_b64,
        simulate_confidence=schema.simulate_confidence,
        simulate_liveness=schema.simulate_liveness,
        actor_id=current_user.id,
        accuracy=schema.accuracy,
        captured_at=schema.captured_at,
        user_agent=user_agent,
        ip_address=client_ip
    )
    return APIResponse(
        success=True,
        data={
            "attendance_id": att.id,
            "image_path": att.selfie_image_path,
            "gps": {
                "latitude": att.gps_latitude,
                "longitude": att.gps_longitude
            } if (att.gps_latitude is not None and att.gps_longitude is not None) else None,
            "verification_status": att.verification_status,
            "timestamp": att.check_in_time.isoformat() if att.check_in_time else None,
            # Backwards compatibility fields for old tests
            "id": att.id,
            "status": att.status,
            "gps_status": att.gps_status,
            "confidence_score": att.confidence_score,
            "liveness_score": att.liveness_score,
            "check_in_time": att.check_in_time,
            "verification_method": att.verification_method,
            "provider_name": att.provider_name
        },
        message="Check-in submitted successfully."
    )

@router.post("/{id}/check-out", response_model=APIResponse[AttendanceResponse])
def check_out(
    id: int,
    schema: CheckOutRequest,
    current_user: User = Depends(get_current_active_user),
    service: AttendanceService = Depends(get_attendance_service)
):
    """GPS geofence verified check-out for the current active user."""
    att = service.check_out(
        session_id=id,
        member_id=current_user.id,
        latitude=schema.latitude,
        longitude=schema.longitude,
        verification_status=schema.verification_status,
        actor_id=current_user.id
    )
    return APIResponse(
        success=True,
        data=AttendanceResponse.model_validate(att),
        message="Check-out submitted successfully."
    )

@router.post("/{id}/manual-attendance", response_model=APIResponse[AttendanceResponse])
def manual_attendance(
    id: int,
    member_id: int = Query(...),
    status_val: str = Query(..., alias="status"),
    current_user: User = Depends(require_coordinator),
    service: AttendanceService = Depends(get_attendance_service)
):
    """Allows administrators to manually mark/update attendance status (Excused, Late, Present, Absent)."""
    att = service.submit_manual_attendance(
        session_id=id,
        member_id=member_id,
        status=status_val,
        actor_id=current_user.id
    )
    return APIResponse(
        success=True,
        data=AttendanceResponse.model_validate(att),
        message="Manual attendance record updated."
    )

@router.get("/{id}/attendances", response_model=APIResponse[List[AttendanceResponse]])
def get_session_attendances(
    id: int,
    current_user: User = Depends(require_coordinator),
    service: AttendanceService = Depends(get_attendance_service)
):
    """Retrieve all member attendance rosters for a given session."""
    records = service.repo.get_session_attendances(id)
    payload = [AttendanceResponse.model_validate(r) for r in records]
    return APIResponse(
        success=True,
        data=payload,
        message=f"Retrieved {len(payload)} attendance records."
    )

@router.post("/{id}/approve-attendance", response_model=APIResponse[AttendanceResponse])
def approve_attendance(
    id: int,
    member_id: int = Query(...),
    current_user: User = Depends(require_coordinator),
    ai_service: AIVerificationService = Depends(get_ai_verification_service)
):
    """Allows administrators to manually verify and approve a pending check-in (fallback policy)."""
    att = ai_service.approve_attendance(
        session_id=id,
        member_id=member_id,
        actor_id=current_user.id
    )
    return APIResponse(
        success=True,
        data=AttendanceResponse.model_validate(att),
        message="Pending fallback check-in successfully approved."
    )
