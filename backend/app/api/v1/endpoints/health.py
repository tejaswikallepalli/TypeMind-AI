"""Health check endpoint definition."""

from typing import Dict
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.core.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(default="healthy", description="Current health status of the service")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current running environment")


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns the operational health and version of the TypeMind AI backend service.",
)
async def get_health() -> HealthResponse:
    """Return service health status and version."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )
