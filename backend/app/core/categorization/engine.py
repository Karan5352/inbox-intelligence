"""Categorization orchestrator: deterministic rules first, embeddings second.

Flow per email:
  1. Run the rule stage. If the best rule's confidence >= threshold, use it.
  2. Otherwise fall back to the embedding kNN classifier.
  3. If nothing is confident, return the ``uncategorized`` fallback.

The result always carries ``source`` (rule|ml|fallback) and a human ``reason`` so
the UI can explain *why* an email landed where it did.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from app.config import get_settings
from app.core.categorization import rules
from app.core.categorization.classifier import KnnClassifier, LabeledExample
from app.core.categorization.prototypes import seed_examples
from app.core.categorization.taxonomy import FALLBACK_SLUG


@dataclass
class Verdict:
    category: str
    confidence: float
    source: str  # "rule" | "ml" | "fallback"
    reason: str
    scores: dict[str, float] = field(default_factory=dict)


class CategorizationEngine:
    def __init__(self, rule_threshold: float, k: int) -> None:
        self.rule_threshold = rule_threshold
        self.classifier = KnnClassifier(k=k)

    # --- lifecycle -----------------------------------------------------------
    def fit(self, examples: list[LabeledExample]) -> None:
        self.classifier.fit(examples)

    def ensure_seeded(self) -> None:
        """Fit from built-in prototypes if the classifier is empty."""
        if not self.classifier.is_fitted:
            self.classifier.fit(seed_examples())

    def add_example(self, text: str, label: str) -> None:
        # Seed prototypes first so an incremental add never leaves the classifier
        # holding only a single (correction) example.
        self.ensure_seeded()
        self.classifier.add(text, label)

    # --- inference -----------------------------------------------------------
    def categorize(
        self, *, sender: str, subject: str, body: str, headers: dict | None = None
    ) -> Verdict:
        ctx = rules.RuleContext(sender=sender, subject=subject, body=body, headers=headers or {})

        rule_match = rules.evaluate(ctx)
        if rule_match and rule_match.confidence >= self.rule_threshold:
            return Verdict(
                category=rule_match.category,
                confidence=round(rule_match.confidence, 4),
                source="rule",
                reason=rule_match.reason,
                scores={rule_match.category: rule_match.confidence},
            )

        self.ensure_seeded()
        pred = self.classifier.predict(f"{subject}\n{subject}\n{body}")
        if pred.category != FALLBACK_SLUG and pred.confidence > 0.0:
            reason = f"Most similar to known {pred.category} emails"
            # A weak rule (below threshold) still counts as corroboration.
            if rule_match and rule_match.category == pred.category:
                reason += f"; {rule_match.reason.lower()}"
            return Verdict(pred.category, round(pred.confidence, 4), "ml", reason, pred.scores)

        if rule_match:  # low-confidence rule is better than nothing
            return Verdict(
                rule_match.category,
                round(rule_match.confidence, 4),
                "rule",
                rule_match.reason,
                {rule_match.category: rule_match.confidence},
            )
        return Verdict(FALLBACK_SLUG, 0.0, "fallback", "No confident match found", {})


@lru_cache(maxsize=1)
def get_engine() -> CategorizationEngine:
    s = get_settings()
    return CategorizationEngine(rule_threshold=s.rule_confidence_threshold, k=s.knn_neighbors)
