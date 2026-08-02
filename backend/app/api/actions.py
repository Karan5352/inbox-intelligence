"""Bulk-action endpoint. Dry-run by default."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.action import BulkActionIn, BulkActionResult
from app.services import action_service

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/bulk", response_model=BulkActionResult)
def bulk_action(payload: BulkActionIn, db: Session = Depends(get_db)) -> BulkActionResult:
    try:
        return action_service.run_bulk(db, payload)
    except action_service.ActionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
