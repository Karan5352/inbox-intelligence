# ADR 0002 - kNN over embeddings for the online learning loop

- **Status:** Accepted
- **Date:** 2026-08

## Context

A core feature is "improves from your corrections." That implies the model must incorporate a new
labelled example *while the user watches*, ideally with no visible training step. Candidate models:

- **Logistic regression / linear SVM over embeddings** - strong accuracy, but each correction
  requires a refit to reflect the change.
- **Fine-tuning the embedding model** - far too heavy for interactive, per-correction updates.
- **kNN + centroid over embeddings** - a correction is a single appended vector; the very next
  prediction already reflects it.

## Decision

Use **kNN with a centroid prior** over L2-normalized embeddings. Vectors are normalized so cosine
similarity is a dot product. Prediction is a similarity-weighted vote of the top-k neighbours,
blended with a small per-category centroid term so one stray neighbour can't dominate.

## Consequences

- **Instant learning:** `classifier.add(text, label)` is `O(1)`; no retrain, no pipeline. This is
  what makes the learning loop feel live.
- **Cold start solved:** the classifier is seeded with a handful of prototype phrases per category,
  so it works before any correction exists; corrections are appended on top.
- **Reproducible:** with the hashing fallback embedder, predictions are deterministic, so tests and
  benchmarks are stable.
- **Trade-off:** kNN is memory-resident and scales O(n) per query. Fine at demo/personal-inbox
  scale; a production version at millions of vectors would swap in an ANN index (FAISS/hnswlib)
  behind the same interface. A `LogisticRegression` variant is kept for the benchmark comparison.
