import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("aip.request_middleware")
logging.basicConfig(level=logging.INFO)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to intercept incoming HTTP requests, calculate processing latency,
    and log client IPs, status codes, methods, paths, and completion metrics.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
        except Exception as e:
            process_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request crashed: {request.method} {request.url.path} "
                f"| Client: {request.client.host if request.client else 'unknown'} "
                f"| Latency: {process_time_ms:.2f}ms "
                f"| Exception: {str(e)}"
            )
            raise e
            
        process_time_ms = (time.time() - start_time) * 1000
        
        log_message = (
            f"{request.method} {request.url.path} "
            f"| Status: {response.status_code} "
            f"| Client: {request.client.host if request.client else 'unknown'} "
            f"| Latency: {process_time_ms:.2f}ms"
        )
        
        if response.status_code >= 500:
            logger.error(log_message)
        elif response.status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)
            
        # Expose execution latency in headers for diagnostics
        response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
        
        return response
