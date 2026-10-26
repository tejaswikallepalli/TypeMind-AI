"""Main FastAPI application factory and ASGI entrypoint for TypeMind AI."""

from contextlib import asynccontextmanager
import logging
import time
from typing import AsyncGenerator
import uuid

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.errors import (
    TypeMindException,
    global_exception_handler,
    typemind_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging

logger = logging.getLogger("typemind.api")


class RootInfoResponse(BaseModel):
    """Schema for root application welcome and metadata."""

    name: str = Field(..., description="Application name")
    description: str = Field(..., description="Summary of service purpose")
    version: str = Field(..., description="Engine version")
    docs_url: str = Field(default="/docs", description="Interactive OpenAPI documentation URL")
    api_v1_prefix: str = Field(default="/api/v1", description="Prefix for v1 REST endpoints")


class HealthResponse(BaseModel):
    """Schema for health status endpoint."""

    status: str = Field(default="healthy", description="Current service health")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown hooks."""
    settings = get_settings()
    root_logger = setup_logging(settings.log_level)
    root_logger.info("Starting %s v%s in [%s] mode...", settings.app_name, settings.app_version, settings.environment)
    root_logger.info("Supported Python analysis target: %s", settings.supported_python_version)
    yield
    root_logger.info("Shutting down %s gracefully...", settings.app_name)


def create_app() -> FastAPI:
    """FastAPI application factory.

    Configures:
    - Metadata and documentation endpoints
    - Request tracing and timing middleware
    - Lifespan events
    - CORS middleware
    - Domain and validation exception handlers
    - Versioned API routes
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Machine-learning-assisted semantic analyzer for Python type-error detection",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Request ID and Latency Tracing Middleware
    @app.middleware("http")
    async def request_id_and_timing_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()
        logger.info(
            "Request started: %s %s [id=%s]",
            request.method,
            request.url.path,
            request_id,
        )

        response: Response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "Request finished: %s %s [id=%s] status=%d in %.2fms",
            request.method,
            request.url.path,
            request_id,
            response.status_code,
            duration_ms,
        )
        return response

    # Cross-Origin Resource Sharing (CORS) Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Exception Handlers
    app.add_exception_handler(TypeMindException, typemind_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # Root Endpoint: GET /
    @app.get(
        "/",
        response_model=RootInfoResponse,
        status_code=status.HTTP_200_OK,
        summary="Application Information",
        description="Returns application name, description, documentation link, and API version.",
        tags=["General"],
    )
    async def get_root() -> RootInfoResponse:
        return RootInfoResponse(
            name=settings.app_name,
            description="Machine-learning-assisted semantic analyzer for Python type-error detection",
            version=settings.app_version,
            docs_url="/docs",
            api_v1_prefix=settings.api_v1_prefix,
        )

    # Health Check Endpoint: GET /health
    @app.get(
        "/health",
        response_model=HealthResponse,
        status_code=status.HTTP_200_OK,
        summary="Service Health",
        description="Returns operational health and version status.",
        tags=["Health"],
    )
    async def get_health() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            environment=settings.environment,
        )

    # Mount API v1 router under /api/v1
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    return app


# Export ASGI application instance
app = create_app()
