from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/info", response_model=APIResponse)
def get_system_info():
    """
    Fetch diagnostics details, version settings, and environment details.
    """
    system_stats = {
        "app_name": settings.APP_NAME,
        "version": "1.0.0",
        "api_v1_prefix": settings.API_V1_STR,
        "debug": settings.DEBUG,
        "server_time": datetime.now(timezone.utc).isoformat(),
        "status": "operational",
        "environment": {
            "platform": "Windows",
            "cpu_usage_mock": "4.2%",
            "memory_usage_mock": "124 MB",
            "database_connected": False,
        }
    }
    return APIResponse(
        success=True,
        data=system_stats,
        message="System diagnostic stats retrieved successfully."
    )
