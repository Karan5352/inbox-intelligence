"""The learning loop: turn a user correction into a new training example, and
measure whether the model actually improves.

Applying a correction:
  1. records the correction (audit + training example),
  2. re-labels the email as user-owned (source='correction', never auto-overwritten),
  3. incrementally teaches the classifier the new example,
  4. snapshots accuracy on the held-out labelled set so the Insights page can plot
     a real learning curve.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.categorization import embeddings
from app.core.categorization.engine import get_engine
from app.models.correction import Correction
from app.models.email import Email
from app.models.metric import Metric
from app.repositories import correction_repo, email_repo, metric_repo
from app.schemas.category import LearningStatus


class CorrectionError(ValueError):
    pass


def apply_correction(db: Session, *, email_id: int, to_category: str) -> Correction:
    email = email_repo.get(db, email_id)
    if email is None:
        raise CorrectionError(f"Email {email_id} not found")

    from_category = email.category
    correction = Correction(
        email_id=email.id,
        from_category=from_category,
        to_category=to_category,
        content=email.content(),
    )
    correction_repo.add(db, correction)

    # The email now reflects the user's decision and is protected from re-labelling.
    email.category = to_category
    email.category_source = "correction"
    email.confidence = 1.0
    email.reason = "Corrected by you"
    email.secondary = []

    # Teach the live classifier immediately (no full retrain needed).
    get_engine().add_example(email.content(), to_category)

    snapshot_accuracy(db, label="correction")
    db.commit()
    return correction


def snapshot_accuracy(db: Session, *, label: str) -> Metric | None:
    """Score the engine against synthetic ground truth and store a Metric.

    Only demo data carries ground-truth labels, so this powers the learning curve
    in demo mode. A real inbox has nothing to score against, so it returns None and
    the Insights page shows a corrections summary instead.
    """
    labelled = [e for e in db.query(Email).all() if e.true_category]
    if not labelled:
        return None

    engine = get_engine()
    correct = 0
    per_cat: dict[str, dict[str, int]] = {}
    for e in labelled:
        pred = engine.categorize(
            sender=e.sender, subject=e.subject, body=e.body, headers=e.headers or {}
        )
        truth = e.true_category or ""
        bucket = per_cat.setdefault(truth, {"correct": 0, "total": 0})
        bucket["total"] += 1
        if pred.category == truth:
            correct += 1
            bucket["correct"] += 1

    accuracy = correct / len(labelled)
    recalls = [b["correct"] / b["total"] for b in per_cat.values() if b["total"]]
    macro = sum(recalls) / len(recalls) if recalls else 0.0

    metric = Metric(
        label=label,
        accuracy=round(accuracy, 4),
        macro_f1=round(macro, 4),
        num_corrections=correction_repo.count(db),
        num_examples=len(labelled),
        detail=per_cat,
    )
    metric_repo.add(db, metric)
    return metric


def status(db: Session) -> LearningStatus:
    from app.core.categorization.prototypes import seed_examples

    latest = metric_repo.latest(db)
    size = get_engine().classifier.size
    corrections = correction_repo.count(db)
    prototypes = len(seed_examples())
    return LearningStatus(
        classifier_examples=size,
        from_prototypes=prototypes,
        from_inbox=max(0, size - prototypes - corrections),
        corrections=corrections,
        embedding_backend=embeddings.backend_name(),
        latest_accuracy=latest.accuracy if latest else None,
    )
