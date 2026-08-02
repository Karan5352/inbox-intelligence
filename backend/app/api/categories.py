"""Category taxonomy + per-category counts."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.categorization.taxonomy import CATEGORIES
from app.db.session import get_db
from app.schemas.category import CategoryOut
from app.services import insights_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryOut]:
    counts = {c.category: c for c in insights_service.category_summary(db)}
    out: list[CategoryOut] = []
    for cat in CATEGORIES:
        summary = counts.get(cat.slug)
        out.append(
            CategoryOut(
                slug=cat.slug,
                name=cat.name,
                color=cat.color,
                icon=cat.icon,
                description=cat.description,
                count=summary.count if summary else 0,
                unread=summary.unread if summary else 0,
            )
        )
    return out
