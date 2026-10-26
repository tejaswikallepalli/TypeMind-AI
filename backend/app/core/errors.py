"""Custom exception definitions and FastAPI exception handlers."""

import logging
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("typemind.errors")


class TypeMindException(Exception):
    """Base exception class for all TypeMind AI errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class SemanticAnalysisError(TypeMindException):
    """Raised when semantic AST analysis encounters an unrecoverable syntax or parse failure."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        status_code = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)
        super().__init__(
            message=message,
            status_code=status_code,
            details=details,
        )


class ModelInferenceError(TypeMindException):
    """Raised when the ML model fails during feature extraction or classification."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


class ValidationError(TypeMindException):
    """Raised when input source code or parameter validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


from fastapi.exceptions import RequestValidationError


async def typemind_exception_handler(request: Request, exc: TypeMindException) -> JSONResponse:
    """Handle domain-specific TypeMind exceptions gracefully."""
    logger.error("TypeMindException occurred: %s (status=%d)", exc.message, exc.status_code, exc_info=True)
    request_id = getattr(request.state, "request_id", None)
    content: Dict[str, Any] = {
        "status": "error",
        "error_type": exc.__class__.__name__,
        "message": exc.message,
        "details": exc.details,
        "path": str(request.url.path),
    }
    if request_id:
        content["request_id"] = request_id
    return JSONResponse(status_code=exc.status_code, content=content)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic request validation errors cleanly with standard structure."""
    request_id = getattr(request.state, "request_id", None)
    status_code = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)
    content: Dict[str, Any] = {
        "status": "error",
        "error_type": "ValidationError",
        "message": "Input validation failed",
        "detail": exc.errors(),
        "details": exc.errors(),
        "path": str(request.url.path),
    }
    if request_id:
        content["request_id"] = request_id
    logger.warning("Request validation failed on %s: %s", request.url.path, exc.errors())
    return JSONResponse(status_code=status_code, content=content)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for unhandled exceptions."""
    logger.critical("Unhandled unexpected exception: %s", str(exc), exc_info=True)
    request_id = getattr(request.state, "request_id", None)
    content: Dict[str, Any] = {
        "status": "error",
        "error_type": "InternalServerError",
        "message": "An unexpected error occurred during processing.",
        "path": str(request.url.path),
    }
    if request_id:
        content["request_id"] = request_id
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content,
    )

