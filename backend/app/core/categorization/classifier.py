"""Embedding-based classifier: k-nearest-neighbours with a centroid prior.

Chosen over a parametric model because *learning from a correction is trivial* -
you append one labelled vector and the next prediction already reflects it, with
no retraining step. Vectors are L2-normalized, so cosine similarity is a dot
product.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.core.categorization.embeddings import embed


@dataclass
class Prediction:
    category: str
    confidence: float
    scores: dict[str, float] = field(default_factory=dict)


@dataclass
class LabeledExample:
    text: str
    label: str


class KnnClassifier:
    def __init__(self, k: int = 5) -> None:
        self.k = k
        self._X: np.ndarray | None = None  # (n, dim) normalized embeddings
        self._labels: list[str] = []
        self._centroids: dict[str, np.ndarray] = {}

    @property
    def is_fitted(self) -> bool:
        return self._X is not None and len(self._labels) > 0

    @property
    def size(self) -> int:
        return len(self._labels)

    def fit(self, examples: list[LabeledExample]) -> None:
        if not examples:
            self._X, self._labels, self._centroids = None, [], {}
            return
        self._labels = [e.label for e in examples]
        self._X = embed([e.text for e in examples])
        self._recompute_centroids()

    def add(self, text: str, label: str) -> None:
        """Incrementally add one labelled example (used by the learning loop)."""
        vec = embed([text])
        self._X = vec if self._X is None else np.vstack([self._X, vec])
        self._labels.append(label)
        self._recompute_centroids()

    def _recompute_centroids(self) -> None:
        assert self._X is not None
        self._centroids = {}
        arr = np.asarray(self._labels)
        for label in set(self._labels):
            self._centroids[label] = self._X[arr == label].mean(axis=0)

    def predict(self, text: str) -> Prediction:
        if not self.is_fitted:
            return Prediction("uncategorized", 0.0, {})
        return self.predict_from_vector(embed([text])[0])

    def predict_from_vector(self, q: np.ndarray) -> Prediction:
        if not self.is_fitted:
            return Prediction("uncategorized", 0.0, {})
        assert self._X is not None

        sims = self._X @ q  # cosine similarity (all vectors normalized)

        # Top-k neighbour vote, weighted by similarity clamped to [0, 1].
        k = min(self.k, len(self._labels))
        top = np.argsort(sims)[::-1][:k]
        votes: dict[str, float] = {}
        for idx in top:
            weight = max(0.0, float(sims[idx]))
            votes[self._labels[idx]] = votes.get(self._labels[idx], 0.0) + weight

        # Blend in a small centroid prior so a single stray neighbour can't dominate.
        for label, centroid in self._centroids.items():
            votes[label] = votes.get(label, 0.0) + 0.25 * max(0.0, float(centroid @ q))

        total = sum(votes.values()) or 1.0
        scores = {label: round(v / total, 4) for label, v in votes.items()}
        best = max(scores, key=scores.get)  # type: ignore[arg-type]
        return Prediction(best, scores[best], scores)
