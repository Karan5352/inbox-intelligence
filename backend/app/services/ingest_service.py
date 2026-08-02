"""Ingest emails from a source into the DB, categorizing each on the way in."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.text import clean_email_text
from app.ingest.base import EmailSource, RawEmail
from app.ingest.demo import DemoSource
from app.ingest.gmail import GmailSource
from app.models.email import Email
from app.repositories import email_repo
from app.services import categorization_service


def _to_model(raw: RawEmail) -> Email:
    body = clean_email_text(raw.body)  # strip HTML, quoted threads, signatures
    return Email(
        message_id=raw.message_id,
        sender=raw.sender,
        sender_name=raw.sender_name,
        recipient=raw.recipient,
        subject=raw.subject,
        body=body,
        snippet=(raw.snippet or body)[:140],
        headers=raw.headers,
        received_at=raw.received_at,
        is_read=raw.is_read,
        true_category=raw.true_category,
    )


def ingest(db: Session, source: EmailSource, *, limit: int) -> int:
    """Fetch from a source, categorize, and persist new emails. Returns count added."""
    categorization_service.rebuild_engine(db)
    added = 0
    for raw in source.fetch(limit):
        if email_repo.get_by_message_id(db, raw.message_id):
            continue  # dedupe
        email = _to_model(raw)
        categorization_service.categorize_email(email)
        email_repo.add(db, email)
        added += 1
    db.commit()
    return added


def active_source() -> tuple[EmailSource, str]:
    """The source the app pulls from: synthetic demo, or Gmail when configured."""
    settings = get_settings()
    if settings.demo_mode:
        return DemoSource(), "demo"
    return GmailSource(settings.gmail_address, settings.gmail_app_password), "gmail"


def sync(db: Session, *, limit: int | None = None, reset: bool = False) -> tuple[str, int]:
    """Pull from whichever source is active and return (source_kind, added).

    When reset is True, clear existing emails first, so the inbox (and every stat
    computed from it) reflects only the current source.
    """
    source, kind = active_source()
    settings = get_settings()
    if limit is None:
        limit = settings.gmail_fetch_limit if kind == "gmail" else 240
    if reset:
        email_repo.clear(db)
    added = ingest(db, source, limit=limit)
    # Learn from the confident rule labels in this batch, then re-sort the emails
    # the model was unsure about against those real examples.
    categorization_service.recategorize_all(db)
    return kind, added
