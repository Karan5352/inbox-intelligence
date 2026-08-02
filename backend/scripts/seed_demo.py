"""Build the synthetic demo database.

Usage (from the backend/ dir, with the venv active):
    python -m scripts.seed_demo [--count N] [--reset]
"""

from __future__ import annotations

import argparse

from app.db.base import Base
from app.db.session import SessionLocal, create_all, engine
from app.ingest.demo import DemoSource
from app.services import ingest_service, learning_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the synthetic demo inbox.")
    parser.add_argument("--count", type=int, default=240, help="Number of emails to generate.")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables first.")
    args = parser.parse_args()

    if args.reset:
        Base.metadata.drop_all(bind=engine)
    create_all()

    with SessionLocal() as db:
        added = ingest_service.ingest(db, DemoSource(), limit=args.count)
        # Record a baseline accuracy snapshot so the learning curve has a start point.
        metric = learning_service.snapshot_accuracy(db, label="baseline")
        db.commit()

    print(f"Seeded {added} synthetic emails.")
    if metric:
        print(
            f"Baseline accuracy on labelled set: {metric.accuracy:.1%} "
            f"(macro recall {metric.macro_f1:.1%}, n={metric.num_examples})"
        )


if __name__ == "__main__":
    main()
