from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from app.models.user import User
from app.api.deps import get_current_active_user, get_notification_service
from app.services.notification import NotificationService
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/", response_model=APIResponse)
def list_notifications(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    Fetch the latest notifications for the current active session user.
    """
    records = service.get_user_notifications(user_id=current_user.id, limit=limit)
    payload = []
    for r in records:
        payload.append({
            "id": r.id,
            "title": r.title,
            "message": r.message,
            "type": r.type,
            "is_read": r.is_read,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    return APIResponse(
        success=True,
        data=payload,
        message=f"Retrieved {len(payload)} notifications."
    )

@router.post("/{id}/read", response_model=APIResponse)
def mark_read(
    id: int,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    Mark a notification as read.
    """
    notif = service.mark_as_read(notif_id=id, user_id=current_user.id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return APIResponse(
        success=True,
        data={"id": notif.id, "is_read": notif.is_read},
        message="Notification marked as read."
    )

@router.post("/clear", response_model=APIResponse)
def clear_all_notifications(
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    Clears all notification logs for the current active user.
    """
    service.clear_all(user_id=current_user.id)
    return APIResponse(
        success=True,
        data=None,
        message="All notifications cleared successfully."
    )
