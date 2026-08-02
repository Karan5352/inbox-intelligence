"""Data access for corrections."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.correction import Correction


def add(db: Session, correction: Correction) -> Correction:
    db.add(correction)
    db.flush()
    return correction


def all_corrections(db: Session) -> Sequence[Correction]:
    return db.scalars(select(Correction).order_by(Correction.created_at)).all()


def count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Correction)) or 0
