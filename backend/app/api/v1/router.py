"""Central API v1 router mounting all v1 endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints.analyze import router as analyze_router
from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.info import router as info_router
from app.api.v1.endpoints.languages import router as languages_router
from app.api.v1.endpoints.model import router as model_router

api_v1_router = APIRouter()

# Mount health endpoint under /api/v1/health
api_v1_router.include_router(health_router, tags=["Health"])

# Mount info endpoint under /api/v1/info
api_v1_router.include_router(info_router, tags=["Project Info"])

# Mount analyze endpoint under /api/v1/analyze
api_v1_router.include_router(analyze_router, tags=["Semantic Analysis"])

# Mount languages endpoint under /api/v1/languages
api_v1_router.include_router(languages_router, tags=["Multi-Language"])

# Mount diagnostics categories endpoint under /api/v1/diagnostics/categories
api_v1_router.include_router(categories_router, prefix="/diagnostics", tags=["Diagnostics"])

# Mount model info endpoint under /api/v1/model/info
api_v1_router.include_router(model_router, prefix="/model", tags=["Machine Learning"])
