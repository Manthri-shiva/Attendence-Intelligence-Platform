from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """
    Standardized API response envelope for all endpoints.
    Enforces clean JSON payloads with status flags, typed data, and structured errors.
    """
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    errors: Optional[List[Any]] = None
