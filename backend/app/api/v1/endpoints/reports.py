from fastapi import APIRouter, Depends, Query, Response, HTTPException
from typing import Optional
from datetime import date
from app.models.user import User
from app.api.deps import get_current_active_user, get_report_service, require_coordinator
from app.services.report import ReportService

router = APIRouter()

@router.get("/export")
def export_report(
    format: str = Query(..., description="csv, excel, pdf"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    department_id: Optional[int] = Query(None),
    team_id: Optional[int] = Query(None),
    member_id: Optional[int] = Query(None),
    session_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_coordinator),
    service: ReportService = Depends(get_report_service)
):
    """
    Downloads timesheets and reports. Scopes data bounds to the coordinator's organization.
    """
    org_id = current_user.organization_id if current_user.role != "SystemAdmin" else None
    
    try:
        content_bytes, mime_type = service.generate_attendance_report(
            format_type=format,
            start_date=start_date,
            end_date=end_date,
            organization_id=org_id,
            department_id=department_id,
            team_id=team_id,
            member_id=member_id,
            session_id=session_id,
            status=status,
            actor_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Resolve correct extension
    ext = "csv"
    fmt_lower = format.strip().lower()
    if fmt_lower == "pdf":
        ext = "html" # PDF-HTML print-ready file
    elif fmt_lower == "excel" or fmt_lower == "xlsx":
        ext = "xls"

    filename = f"attendance_report_{date.today().strftime('%Y%m%d')}.{ext}"

    return Response(
        content=content_bytes,
        media_type=mime_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
