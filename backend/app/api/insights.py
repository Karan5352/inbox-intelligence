"""Insights / analytics endpoint for the dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.insight import InsightsOut
from app.services import insights_service

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("", response_model=InsightsOut)
def get_insights(db: Session = Depends(get_db)) -> InsightsOut:
    return insights_service.build_insights(db)
