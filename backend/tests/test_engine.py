"""Tests for the classifier and the orchestration engine."""

from __future__ import annotations

from app.core.categorization.classifier import KnnClassifier, LabeledExample
from app.core.categorization.engine import CategorizationEngine


def test_knn_learns_from_examples():
    clf = KnnClassifier(k=3)
    clf.fit(
        [
            LabeledExample("invoice payment due balance", "finance"),
            LabeledExample("your package shipped tracking", "shipping"),
            LabeledExample("meeting roadmap sprint review", "work"),
        ]
    )
    assert clf.predict("please pay this invoice balance").category == "finance"
    assert clf.predict("track my shipped package").category == "shipping"


def test_knn_incremental_add_changes_prediction():
    clf = KnnClassifier(k=1)
    clf.fit([LabeledExample("hello there friend", "personal")])
    clf.add("quarterly financial report earnings", "finance")
    assert clf.predict("quarterly earnings financial").category == "finance"


def test_engine_prefers_high_confidence_rule():
    engine = CategorizationEngine(rule_threshold=0.8, k=5)
    v = engine.categorize(sender="ship@amazon.com", subject="Order", body="has shipped tracking")
    assert v.source == "rule" and v.category == "shipping"


def test_engine_falls_back_to_ml_and_seeds_itself():
    engine = CategorizationEngine(rule_threshold=0.95, k=5)  # high bar -> rules rarely win
    v = engine.categorize(
        sender="friend@gmail.com", subject="dinner this weekend", body="are we still on for dinner"
    )
    assert v.source in {"ml", "rule"}
    assert engine.classifier.is_fitted  # ensure_seeded fired
    assert v.reason  # always explains itself


def test_verdict_always_has_reason_and_source():
    engine = CategorizationEngine(rule_threshold=0.8, k=5)
    v = engine.categorize(sender="x@y.com", subject="", body="")
    assert v.source in {"rule", "ml", "fallback"}
    assert isinstance(v.reason, str) and v.reason
