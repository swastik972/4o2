"""
Health-check endpoint.
"""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
def health_check():
    """Return application health status."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "app_name": settings.app_name,
        "debug": settings.debug,
    }
