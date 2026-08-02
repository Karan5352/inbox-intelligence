"""Shared pytest fixtures. Each test run gets an isolated SQLite database.

The DATABASE_URL env var is set *before* any app module is imported so the
engine binds to the throwaway file rather than the developer's demo DB.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest

# Must run before `app.config` is imported anywhere.
_TMP_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)  # noqa: SIM115 (kept open for the run)
_TMP_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.name}"
os.environ["DEMO_MODE"] = "true"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.categorization.engine import get_engine  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.ingest.demo import DemoSource  # noqa: E402
from app.main import app  # noqa: E402
from app.services import ingest_service  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db() -> Iterator[None]:
    """Recreate the schema and reset the in-memory engine before every test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    get_engine.cache_clear()
    yield


@pytest.fixture
def db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


@pytest.fixture
def seeded_db(db: Session) -> Session:
    ingest_service.ingest(db, DemoSource(), limit=60)
    return db


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:  # context manager -> lifespan seeds the engine
        yield c


@pytest.fixture
def seeded_client(client: TestClient) -> TestClient:
    with SessionLocal() as session:
        ingest_service.ingest(session, DemoSource(), limit=60)
    return client
