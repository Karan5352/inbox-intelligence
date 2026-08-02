"""Manage and run automation workflows over the inbox."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.automation import rules as automation_rules
from app.models.automation import Automation
from app.models.email import Email
from app.repositories import automation_repo
from app.schemas.action import AutomationIn, AutomationRunResult


def create(db: Session, payload: AutomationIn) -> Automation:
    automation = Automation(
        name=payload.name,
        enabled=payload.enabled,
        priority=payload.priority,
        condition=payload.condition.model_dump(),
        action=payload.action.model_dump(),
    )
    automation_repo.add(db, automation)
    db.commit()
    return automation


def delete(db: Session, automation_id: int) -> bool:
    automation = automation_repo.get(db, automation_id)
    if automation is None:
        return False
    automation_repo.delete(db, automation)
    db.commit()
    return True


def _email_view(email: Email) -> dict:
    return {
        "category": email.category,
        "sender": email.sender,
        "subject": email.subject,
        "is_read": email.is_read,
    }


def _apply_action(email: Email, action: dict) -> None:
    match action.get("type"):
        case "label":
            label = (action.get("value") or "").strip()
            if label and label not in email.labels:
                email.labels = [*email.labels, label]
        case "archive":
            email.is_archived = True
        case "mark_read":
            email.is_read = True
        case "recategorize":
            target = (action.get("value") or "").strip()
            if target:
                email.category = target
                email.category_source = "correction"
                email.reason = "Set by automation"


def run_all(db: Session, *, dry_run: bool = True) -> AutomationRunResult:
    """Evaluate every enabled automation against every non-archived email."""
    automations = list(automation_repo.list_all(db, enabled_only=True))
    emails = db.query(Email).filter(Email.is_archived.is_(False)).all()

    matched = 0
    applied = 0
    by_automation: dict[str, int] = {}
    for automation in automations:
        hits = 0
        for email in emails:
            if automation_rules.matches(automation.condition, _email_view(email)):
                matched += 1
                hits += 1
                if not dry_run:
                    _apply_action(email, automation.action)
                    applied += 1
        by_automation[automation.name] = hits
        if not dry_run and hits:
            automation.run_count += hits

    if not dry_run:
        db.commit()
    return AutomationRunResult(
        dry_run=dry_run, matched=matched, applied=applied, by_automation=by_automation
    )
