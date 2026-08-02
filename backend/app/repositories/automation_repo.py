"""Data access for automations."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.automation import Automation


def add(db: Session, automation: Automation) -> Automation:
    db.add(automation)
    db.flush()
    return automation


def get(db: Session, automation_id: int) -> Automation | None:
    return db.get(Automation, automation_id)


def list_all(db: Session, *, enabled_only: bool = False) -> Sequence[Automation]:
    stmt = select(Automation).order_by(Automation.priority, Automation.id)
    if enabled_only:
        stmt = stmt.where(Automation.enabled.is_(True))
    return db.scalars(stmt).all()


def delete(db: Session, automation: Automation) -> None:
    db.delete(automation)
    db.flush()
