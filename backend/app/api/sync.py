"""Inbox sync endpoint. Pulls from the active source (demo or Gmail) and categorizes.

The active source is chosen by config: synthetic demo data unless DEMO_MODE is
false and Gmail credentials are present.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.ingest.gmail import GmailConfigError
from app.services import ingest_service

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("")
def sync_inbox(
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, ge=1, le=500),
    reset: bool = Query(
        default=False, description="Clear existing mail first (for switching source)."
    ),
) -> dict:
    try:
        kind, added = ingest_service.sync(db, limit=limit, reset=reset)
    except GmailConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - surface source/connection errors cleanly
        raise HTTPException(status_code=502, detail=f"Sync failed: {exc}") from exc
    return {"source": kind, "added": added, "reset": reset}
