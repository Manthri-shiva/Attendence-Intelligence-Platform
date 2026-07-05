from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from app.schemas.response import APIResponse

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Format standard HTTPExceptions into APIResponse envelopes.
    """
    response_content = APIResponse(
        success=False,
        message=str(exc.detail),
        errors=[{"detail": exc.detail}]
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response_content.model_dump()
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Format Pydantic request validation exceptions into standard APIResponse structures.
    """
    errors_list = []
    for err in exc.errors():
        errors_list.append({
            "loc": list(err.get("loc", [])),
            "msg": err.get("msg", ""),
            "type": err.get("type", "")
        })
        
    response_content = APIResponse(
        success=False,
        message="Validation failed",
        errors=errors_list
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_content.model_dump()
    )

from app.core.domain_exceptions import (
    DomainException, UserNotFoundError, InvalidCredentialsError, InactiveUserError,
    TokenExpiredOrInvalidError, ObjectNotFoundError, DuplicateRecordError, PermissionDeniedError
)

async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """
    Format AIP domain exceptions raised by the service layer into envelopes.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, (UserNotFoundError, ObjectNotFoundError)):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, PermissionDeniedError):
        status_code = status.HTTP_403_FORBIDDEN
        
    response_content = APIResponse(
        success=False,
        message=exc.message,
        errors=[{"detail": exc.message, "type": exc.__class__.__name__}]
    )
    return JSONResponse(
        status_code=status_code,
        content=response_content.model_dump()
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Format generic, uncaught exceptions into standard 500 APIResponse structures.
    """
    response_content = APIResponse(
        success=False,
        message="Internal server error occurred",
        errors=[{"msg": str(exc), "type": "server_error"}]
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_content.model_dump()
    )

def setup_exception_handlers(app) -> None:
    """
    Configure global exception hooks on a FastAPI application instance.
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

