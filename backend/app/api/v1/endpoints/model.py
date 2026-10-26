"""Machine Learning model information endpoint definition."""

from fastapi import APIRouter, Depends, status

from app.schemas.ml import ModelInfoResponse
from app.services.model import ModelService, get_model_service

router = APIRouter()


@router.get(
    "/info",
    response_model=ModelInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="ML Model Architecture and Metadata",
    description=(
        "Returns the active Machine Learning type classifier metadata, architecture, "
        "trained classes, feature count, and held-out evaluation summary. "
        "Gracefully indicates 'unavailable' if the model artifact is not loaded."
    ),
)
async def get_model_information(
    service: ModelService = Depends(get_model_service),
) -> ModelInfoResponse:
    """Return machine learning model lineage, evaluation metrics, and operational status."""
    return service.get_model_info()
