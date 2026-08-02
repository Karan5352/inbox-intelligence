"""Data access for accuracy metrics."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.metric import Metric


def add(db: Session, metric: Metric) -> Metric:
    db.add(metric)
    db.flush()
    return metric


def all_metrics(db: Session) -> Sequence[Metric]:
    return db.scalars(select(Metric).order_by(Metric.created_at)).all()


def latest(db: Session) -> Metric | None:
    return db.scalar(select(Metric).order_by(Metric.created_at.desc()).limit(1))
