"""Diagnostic categories endpoint definition."""

from fastapi import APIRouter, Depends, status

from app.schemas.diagnostics import CategoriesResponse
from app.services.diagnostics import CategoryService, get_category_service

router = APIRouter()


@router.get(
    "/categories",
    response_model=CategoriesResponse,
    status_code=status.HTTP_200_OK,
    summary="List Diagnostic Categories",
    description=(
        "Returns all supported diagnostic error categories, their descriptions, "
        "associated rule IDs, default severity levels, and automated fix availability."
    ),
)
async def list_diagnostic_categories(
    service: CategoryService = Depends(get_category_service),
) -> CategoriesResponse:
    """Return all recognized semantic diagnostic categories."""
    return service.get_categories()
