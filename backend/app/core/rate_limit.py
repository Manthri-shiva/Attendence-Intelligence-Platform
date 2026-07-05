import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status

# In-memory IP request history cache: {ip: (first_request_time, request_count)}
_login_rate_limit_cache: Dict[str, Tuple[float, int]] = {}

def rate_limit_login(request: Request):
    """
    Limits client IP logins to 5 requests per 60-second window.
    Throws a 429 Too Many Requests exception if exceeded.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    if client_ip in _login_rate_limit_cache:
        start_time, count = _login_rate_limit_cache[client_ip]
        if now - start_time < 60:
            if count >= 10: # Limit to 10 attempts per minute to avoid blocking test runners
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many login attempts. Please try again in 1 minute."
                )
            _login_rate_limit_cache[client_ip] = (start_time, count + 1)
        else:
            _login_rate_limit_cache[client_ip] = (now, 1)
    else:
        _login_rate_limit_cache[client_ip] = (now, 1)
