"""Bulk actions over a set of emails. Dry-run by default - actions preview their
effect and only mutate when the caller explicitly opts in (``dry_run=False``).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.categorization.taxonomy import is_valid
from app.models.email import Email
from app.repositories import email_repo
from app.schemas.action import BulkActionIn, BulkActionResult


class ActionError(ValueError):
    pass


def _resolve_ids(db: Session, payload: BulkActionIn) -> list[int]:
    if payload.email_ids:
        return payload.email_ids
    if payload.category:
        return email_repo.ids_for(db, category=payload.category)
    return []


def _apply_one(email: Email, payload: BulkActionIn) -> None:
    match payload.action:
        case "archive":
            email.is_archived = True
        case "unarchive":
            email.is_archived = False
        case "mark_read":
            email.is_read = True
        case "mark_unread":
            email.is_read = False
        case "label":
            label = (payload.value or "").strip()
            if label and label not in email.labels:
                email.labels = [*email.labels, label]
        case "recategorize":
            target = (payload.value or "").strip()
            if not is_valid(target):
                raise ActionError(f"Unknown category: {target}")
            email.category = target
            email.category_source = "correction"
            email.confidence = 1.0
            email.reason = "Set via bulk action"
        case "delete":
            pass  # handled at the collection level


def run_bulk(db: Session, payload: BulkActionIn) -> BulkActionResult:
    ids = _resolve_ids(db, payload)
    emails = [e for e in (email_repo.get(db, i) for i in ids) if e is not None]

    if payload.dry_run:
        return BulkActionResult(
            action=payload.action,
            dry_run=True,
            affected=len(emails),
            email_ids=[e.id for e in emails],
            message=f"Would {payload.action.replace('_', ' ')} {len(emails)} email(s).",
        )

    if payload.action == "delete":
        for e in emails:
            db.delete(e)
    else:
        for e in emails:
            _apply_one(e, payload)
    db.commit()
    verb = payload.action.replace("_", " ").capitalize()
    return BulkActionResult(
        action=payload.action,
        dry_run=False,
        affected=len(emails),
        email_ids=[e.id for e in emails],
        message=f"{verb} applied to {len(emails)} email(s).",
    )
