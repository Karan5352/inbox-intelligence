"""Health + service metadata endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.core.categorization import embeddings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "demo_mode": settings.demo_mode,
        "embedding_backend": embeddings.backend_name(),
    }
