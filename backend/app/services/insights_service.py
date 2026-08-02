"""Aggregate inbox analytics for the dashboard."""

from __future__ import annotations

from collections import Counter, defaultdict

from sqlalchemy.orm import Session

from app.core.categorization.taxonomy import BY_SLUG, CATEGORIES
from app.core.insights.aggregate import needs_reply
from app.models.email import Email
from app.repositories import metric_repo
from app.schemas.insight import (
    AccuracyPoint,
    CategoryCount,
    InsightsOut,
    SenderCount,
    VolumePoint,
)


def build_insights(db: Session) -> InsightsOut:
    emails = db.query(Email).all()
    total = len(emails)
    unread = sum(1 for e in emails if not e.is_read)
    archived = sum(1 for e in emails if e.is_archived)
    needs = sum(
        1
        for e in emails
        if needs_reply(category=e.category, is_read=e.is_read, is_archived=e.is_archived)
    )

    # Per-category counts, in taxonomy order (only categories that appear).
    cat_total: Counter[str] = Counter(e.category for e in emails)
    cat_unread: Counter[str] = Counter(e.category for e in emails if not e.is_read)
    by_category = [
        CategoryCount(
            category=c.slug,
            name=c.name,
            color=c.color,
            count=cat_total.get(c.slug, 0),
            unread=cat_unread.get(c.slug, 0),
        )
        for c in CATEGORIES
        if cat_total.get(c.slug, 0) > 0
    ]

    # Top senders.
    sender_counts: Counter[str] = Counter(e.sender for e in emails)
    name_by_sender = {e.sender: e.sender_name for e in emails}
    top_senders = [
        SenderCount(sender=s, sender_name=name_by_sender.get(s, ""), count=n)
        for s, n in sender_counts.most_common(8)
    ]

    # Volume by day.
    by_day: dict[str, int] = defaultdict(int)
    for e in emails:
        by_day[e.received_at.date().isoformat()] += 1
    volume_by_day = [VolumePoint(date=d, count=n) for d, n in sorted(by_day.items())]

    # Accuracy trend from stored metrics.
    accuracy_trend = [
        AccuracyPoint(
            label=m.label,
            accuracy=m.accuracy,
            num_corrections=m.num_corrections,
            created_at=m.created_at.isoformat(),
        )
        for m in metric_repo.all_metrics(db)
    ]

    # Rule vs ML attribution.
    rule_vs_ml: dict[str, int] = dict(Counter(e.category_source for e in emails))

    return InsightsOut(
        total_emails=total,
        unread=unread,
        archived=archived,
        needs_reply=needs,
        by_category=by_category,
        top_senders=top_senders,
        volume_by_day=volume_by_day,
        accuracy_trend=accuracy_trend,
        rule_vs_ml=rule_vs_ml,
    )


def category_summary(db: Session) -> list[CategoryCount]:
    """Per-category counts across the whole inbox (used by the /categories endpoint)."""
    rows = db.query(Email.category, Email.is_read).all()
    total: Counter[str] = Counter(c for c, _ in rows)
    unread: Counter[str] = Counter(c for c, r in rows if not r)
    return [
        CategoryCount(
            category=slug,
            name=cat.name,
            color=cat.color,
            count=total[slug],
            unread=unread.get(slug, 0),
        )
        for slug, cat in BY_SLUG.items()
        if total.get(slug, 0)
    ]
