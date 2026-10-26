"""Endpoints package initialization."""

from app.api.v1.endpoints.analyze import router as analyze_router
from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.info import router as info_router
from app.api.v1.endpoints.model import router as model_router

__all__ = [
    "analyze_router",
    "categories_router",
    "health_router",
    "info_router",
    "model_router",
]
