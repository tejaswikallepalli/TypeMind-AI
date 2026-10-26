"""API endpoints for querying supported programming languages and dynamic tool availability."""

import logging
from fastapi import APIRouter, Depends, status

from app.languages.registry import LanguageRegistry, get_language_registry
from app.schemas.languages import LanguagesResponse

logger = logging.getLogger("typemind.api.languages")
router = APIRouter()


@router.get(
    "/languages",
    response_model=LanguagesResponse,
    status_code=status.HTTP_200_OK,
    summary="List Supported Languages & Capabilities",
    description=(
        "Returns all registered programming languages, their file extensions, "
        "required compilers/static analysis tools, live availability on the host, "
        "and setup instructions if missing."
    ),
)
async def list_supported_languages(
    registry: LanguageRegistry = Depends(get_language_registry),
) -> LanguagesResponse:
    """Return configured languages, active toolchains, and operational support tiers."""
    resp = registry.get_languages_response()
    logger.debug("Returned %d registered languages", resp.total)
    return resp
