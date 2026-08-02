"""FastAPI application factory.

Mounts the routers, configures CORS for the Next.js frontend, and on startup
ensures the schema exists and the categorization engine is fitted from whatever
the user has already taught it (prototypes + stored corrections).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import (
    actions,
    automations,
    categories,
    corrections,
    emails,
    health,
    insights,
    sync,
)
from app.config import get_settings
from app.db.session import SessionLocal, create_all
from app.repositories import email_repo
from app.services import categorization_service, ingest_service

DESCRIPTION = """
**Inbox Intelligence** - a privacy-aware email intelligence API.

Hybrid categorization (deterministic rules → local embeddings), a learning loop
that improves from your corrections, bulk actions, automation workflows, and
inbox insights. Runs on synthetic data by default; nothing leaves your machine.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_all()
    settings = get_settings()
    with SessionLocal() as db:
        categorization_service.rebuild_engine(db)
        # When pointed at a real inbox, pull it on first boot so the app is never
        # empty. Best-effort: a bad credential should not stop the server starting.
        if not settings.demo_mode and email_repo.count(db) == 0:
            try:
                ingest_service.sync(db)
            except Exception as exc:  # noqa: BLE001
                logging.getLogger("uvicorn.error").warning("Gmail sync on startup failed: %s", exc)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=DESCRIPTION,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for module in (
        health,
        emails,
        categories,
        corrections,
        actions,
        automations,
        insights,
        sync,
    ):
        app.include_router(module.router)
    return app


app = create_app()
