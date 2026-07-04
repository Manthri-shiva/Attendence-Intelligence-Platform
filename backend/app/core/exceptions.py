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
    app.add_exception_handler(Exception, generic_exception_handler)
