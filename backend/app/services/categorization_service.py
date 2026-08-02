"""Use-case layer for categorization: fit the engine from the DB, categorize, persist.

Keeps the ML engine (pure, no DB) and the persistence layer (repositories) wired
together in one place. The engine is a process-wide singleton; we (re)fit it from
the built-in prototypes plus every stored correction so it always reflects what
the user has taught it.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.categorization.classifier import LabeledExample
from app.core.categorization.engine import get_engine
from app.core.categorization.prototypes import seed_examples
from app.models.email import Email
from app.repositories import correction_repo

# Emails the rules labelled at or above this confidence are trusted enough to use
# as ML training examples (weak supervision). Rules are independent of the model,
# so this is not a self-reinforcing loop; only rule- and user-labelled mail feeds
# back in, never the model's own guesses.
_RULE_EXAMPLE_MIN_CONFIDENCE = 0.85
_MAX_RULE_EXAMPLES = 600


def training_examples(db: Session, *, include_corrections: bool = True) -> list[LabeledExample]:
    """Everything the classifier learns from: prototypes, confident rule labels, and
    (optionally) user corrections.

    The rule-labelled real emails are what let the model adapt to an actual inbox:
    instead of matching mail against synthetic phrases, it matches against real
    examples the deterministic rules were confident about.
    """
    examples = seed_examples()

    rule_labelled = (
        db.query(Email)
        .filter(Email.category_source == "rule", Email.confidence >= _RULE_EXAMPLE_MIN_CONFIDENCE)
        .limit(_MAX_RULE_EXAMPLES)
        .all()
    )
    for e in rule_labelled:
        examples.append(LabeledExample(text=e.content(), label=e.category))

    if include_corrections:
        for c in correction_repo.all_corrections(db):
            examples.append(LabeledExample(text=c.content, label=c.to_category))

    return examples


def rebuild_engine(db: Session) -> int:
    """Fit the classifier from prototypes, confident rule labels, and corrections."""
    engine = get_engine()
    engine.fit(training_examples(db))
    return engine.classifier.size


def _secondary_categories(
    primary: str, scores: dict[str, float], *, max_n: int = 2, rel: float = 0.6, floor: float = 0.15
) -> list[str]:
    """Other categories that scored close to the winner (display only)."""
    top = scores.get(primary, 0.0) or 1.0
    ranked = sorted(
        ((c, s) for c, s in scores.items() if c not in (primary, "uncategorized")),
        key=lambda kv: kv[1],
        reverse=True,
    )
    return [c for c, s in ranked if s >= floor and s >= rel * top][:max_n]


def categorize_email(email: Email) -> None:
    """Categorize a single email in place (mutates category fields)."""
    verdict = get_engine().categorize(
        sender=email.sender, subject=email.subject, body=email.body, headers=email.headers or {}
    )
    email.category = verdict.category
    email.category_source = verdict.source
    email.confidence = verdict.confidence
    email.reason = verdict.reason
    email.secondary = _secondary_categories(verdict.category, verdict.scores)


def recategorize_all(db: Session) -> int:
    """Re-run categorization over every non-corrected email (e.g. after new learning)."""
    rebuild_engine(db)
    emails = db.query(Email).all()
    for email in emails:
        # Don't override an explicit user correction.
        if email.category_source == "correction":
            continue
        categorize_email(email)
    db.commit()
    return len(emails)
