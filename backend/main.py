"""
AI Backend — FastAPI Application Entry Point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging

# ── API routers ─────────────────────────────────────────────────
from app.api.health import router as health_router
from app.api.datasets import router as datasets_router
from app.api.models import router as models_router


# ── Lifespan (startup / shutdown) ───────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise resources on startup, clean up on shutdown."""
    # Startup
    setup_logging()
    logger.info("Starting {} v{}", settings.app_name, settings.app_version)
    init_db()
    logger.info("Database tables created / verified")
    yield
    # Shutdown
    logger.info("Shutting down …")


# ── FastAPI app ─────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered pothole detection backend — Phase 1",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ───────────────────────────────────────────
app.include_router(health_router)
app.include_router(datasets_router)
app.include_router(models_router)


@app.get("/", tags=["Root"])
def root():
    """Root endpoint — basic welcome message."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
    }
