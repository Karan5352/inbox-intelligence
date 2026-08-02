"""Correction endpoint - the entry point to the learning loop."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.categorization.taxonomy import TRAINABLE_SLUGS, is_valid
from app.db.session import get_db
from app.schemas.category import CorrectionIn, CorrectionOut, LearningStatus
from app.services import categorization_service, learning_service

router = APIRouter(tags=["learning"])


@router.post("/corrections", response_model=CorrectionOut, status_code=201)
def create_correction(payload: CorrectionIn, db: Session = Depends(get_db)) -> CorrectionOut:
    if not is_valid(payload.to_category) or payload.to_category not in TRAINABLE_SLUGS:
        raise HTTPException(status_code=422, detail=f"Invalid category: {payload.to_category}")
    try:
        correction = learning_service.apply_correction(
            db, email_id=payload.email_id, to_category=payload.to_category
        )
    except learning_service.CorrectionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CorrectionOut.model_validate(correction, from_attributes=True)


@router.get("/learning/status", response_model=LearningStatus)
def learning_status(db: Session = Depends(get_db)) -> LearningStatus:
    return learning_service.status(db)


@router.post("/recategorize")
def recategorize(db: Session = Depends(get_db)) -> dict:
    """Re-sort every email (except your corrections) using everything learned so far."""
    n = categorization_service.recategorize_all(db)
    return {"recategorized": n}
