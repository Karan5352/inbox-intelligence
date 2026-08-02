"""Database engine and session management."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

_settings = get_settings()

# SQLite needs check_same_thread=False for FastAPI's threadpool; harmless elsewhere.
_connect_args = {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}

# Ensure the sqlite parent directory exists before the engine tries to open it.
if _settings.database_url.startswith("sqlite:///"):
    db_path = Path(_settings.database_url.removeprefix("sqlite:///"))
    db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(_settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all() -> None:
    """Create tables from ORM metadata (used by seeding/tests; Alembic owns prod)."""
    from app import models  # noqa: F401  (register mappers)
    from app.db.base import Base

    Base.metadata.create_all(bind=engine)
