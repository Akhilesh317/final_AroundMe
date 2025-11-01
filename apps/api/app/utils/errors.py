"""Error handling utilities"""
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel


class ProblemDetail(BaseModel):
    """RFC 7807 Problem Details for HTTP APIs"""
    
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None
    trace_id: Optional[str] = None
    extensions: Optional[Dict[str, Any]] = None


class AroundMeException(Exception):
    """Base exception for Around Me"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type: str = "about:blank",
        extensions: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.extensions = extensions or {}
        super().__init__(message)


class ProviderError(AroundMeException):
    """Error from external provider"""
    
    def __init__(self, provider: str, message: str, status_code: int = 502):
        super().__init__(
            message=f"{provider} error: {message}",
            status_code=status_code,
            error_type="provider-error",
            extensions={"provider": provider},
        )


class ValidationError(AroundMeException):
    """Validation error"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        extensions = {"field": field} if field else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type="validation-error",
            extensions=extensions,
        )


class NotFoundError(AroundMeException):
    """Resource not found"""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            status_code=status.HTTP_404_NOT_FOUND,
            error_type="not-found",
            extensions={"resource": resource, "identifier": identifier},
        )


def create_problem_detail(exc: AroundMeException, trace_id: str) -> ProblemDetail:
    """Create RFC 7807 problem detail from exception"""
    return ProblemDetail(
        type=exc.error_type,
        title=exc.__class__.__name__,
        status=exc.status_code,
        detail=exc.message,
        trace_id=trace_id,
        extensions=exc.extensions,
    )