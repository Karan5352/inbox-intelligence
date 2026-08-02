"""Data access for emails. All email DB queries live here (never in routers)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.email import Email


def get(db: Session, email_id: int) -> Email | None:
    return db.get(Email, email_id)


def get_by_message_id(db: Session, message_id: str) -> Email | None:
    return db.scalar(select(Email).where(Email.message_id == message_id))


def list_emails(
    db: Session,
    *,
    category: str | None = None,
    unread: bool | None = None,
    archived: bool | None = False,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[Sequence[Email], int]:
    stmt = select(Email)
    if category:
        stmt = stmt.where(Email.category == category)
    if unread is not None:
        stmt = stmt.where(Email.is_read.is_(not unread))
    if archived is not None:
        stmt = stmt.where(Email.is_archived.is_(archived))
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Email.subject).like(like),
                func.lower(Email.body).like(like),
                func.lower(Email.sender).like(like),
                func.lower(Email.sender_name).like(like),
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Email.received_at.desc()).limit(limit).offset(offset)).all()
    return rows, total


def ids_for(db: Session, *, category: str | None) -> list[int]:
    stmt = select(Email.id).where(Email.is_archived.is_(False))
    if category:
        stmt = stmt.where(Email.category == category)
    return list(db.scalars(stmt).all())


def add(db: Session, email: Email) -> Email:
    db.add(email)
    db.flush()
    return email


def count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Email)) or 0


def clear(db: Session) -> int:
    """Delete all emails (used when switching data source). Returns rows removed."""
    n = count(db)
    db.query(Email).delete()
    db.flush()
    return n
