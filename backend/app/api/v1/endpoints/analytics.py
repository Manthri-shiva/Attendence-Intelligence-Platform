from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.models.user import User
from app.api.deps import get_current_active_user, get_analytics_service
from app.services.analytics import AnalyticsService
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/dashboard", response_model=APIResponse)
def get_dashboard(
    current_user: User = Depends(get_current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Fetch live aggregated dashboard counts and rates.
    Scoped by the current user's organization context if they are a tenant administrator or member.
    """
    org_id = current_user.organization_id if current_user.role != "SystemAdmin" else None
    data = service.get_dashboard_metrics(organization_id=org_id)
    return APIResponse(
        success=True,
        data=data,
        message="Dashboard metrics retrieved successfully."
    )

@router.get("/charts", response_model=APIResponse)
def get_charts(
    current_user: User = Depends(get_current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Fetch daily/weekly/monthly dataset trends for chart renderings.
    Scoped by the current user's organization context.
    """
    org_id = current_user.organization_id if current_user.role != "SystemAdmin" else None
    data = service.get_charts_data(organization_id=org_id)
    return APIResponse(
        success=True,
        data=data,
        message="Charts dataset retrieved successfully."
    )
