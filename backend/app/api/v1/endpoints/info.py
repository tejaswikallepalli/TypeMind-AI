"""Project and API information endpoint."""

from typing import List
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.core.config import get_settings

router = APIRouter()


class ProjectInfoResponse(BaseModel):
    """Detailed metadata about TypeMind AI engine and supported languages."""

    project_name: str = Field(..., description="Name of the application")
    api_version: str = Field(..., description="REST API version")
    app_version: str = Field(..., description="Engine application semantic version")
    supported_language: str = Field(..., description="Primary language analyzed")
    supported_python_version: str = Field(..., description="Supported Python versions")
    features: List[str] = Field(default_factory=list, description="Enabled architectural features")


@router.get(
    "/info",
    response_model=ProjectInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Project and API Metadata",
    description="Returns project name, API version, supported programming languages, and core features.",
)
async def get_project_info() -> ProjectInfoResponse:
    """Return project name, API version, and supported programming language."""
    settings = get_settings()
    return ProjectInfoResponse(
        project_name=settings.app_name,
        api_version="v1",
        app_version=settings.app_version,
        supported_language="Python",
        supported_python_version=settings.supported_python_version,
        features=[
            "ast_semantic_analysis",
            "deterministic_rule_checking",
            "ml_assisted_classification",
            "automated_fix_suggestions",
            "contextual_explanations",
        ],
    )
