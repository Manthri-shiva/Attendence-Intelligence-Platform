from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.middleware import RequestLoggingMiddleware
from app.core.exceptions import setup_exception_handlers

app = FastAPI(
    title=settings.APP_NAME,
    description="Attendance Intelligence Platform (AIP) API Gateway Service",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Register request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Register global exception handlers
setup_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_STR)


# CORS configurations matching settings rules
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/health", tags=["System"])
def health_check():
    """
    Service health check endpoint.
    Used for monitoring deployments and validating server state.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "debug_mode": settings.DEBUG
    }
