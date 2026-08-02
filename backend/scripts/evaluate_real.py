"""Estimate real-world accuracy by hand-labelling a sample of the actual inbox.

Real email has no ground-truth labels, so this is the only honest way to measure
accuracy on real data: you assign the correct category to a random sample, and it
checks how often the categorizer agreed. Nothing about email content is written to
disk except your labels, kept under the gitignored data/local/ directory.

Usage (from backend/, venv active, with a real inbox synced):
    python -m scripts.evaluate_real            # label ~40 emails, then score
    python -m scripts.evaluate_real --count 30
    python -m scripts.evaluate_real --score    # just re-score what you've labelled
"""

from __future__ import annotations

import argparse
import json
import random

from app.config import DATA_DIR
from app.core.categorization.taxonomy import TRAINABLE_SLUGS
from app.db.session import SessionLocal
from app.models.email import Email

LABELS_PATH = DATA_DIR / "local" / "eval_labels.json"
_CATS = list(TRAINABLE_SLUGS)


def _load_labels() -> dict[str, str]:
    if LABELS_PATH.exists():
        return json.loads(LABELS_PATH.read_text())
    return {}


def _save_labels(labels: dict[str, str]) -> None:
    LABELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    LABELS_PATH.write_text(json.dumps(labels, indent=2))


def _menu() -> str:
    return "  ".join(f"{i + 1}:{c}" for i, c in enumerate(_CATS))


def label(count: int) -> None:
    labels = _load_labels()
    with SessionLocal() as db:
        pool = [
            e
            for e in db.query(Email).filter(Email.is_archived.is_(False)).all()
            if e.category_source != "correction" and e.message_id not in labels
        ]
        random.shuffle(pool)
        batch = pool[:count]
        if not batch:
            print("Nothing left to label. Run with --score to see results.")
            return
        print(f"Labelling {len(batch)} emails. Pick the CORRECT category for each.")
        print("Enter a number, or 's' to skip, 'q' to stop and score.\n")
        print(_menu(), "\n")
        for i, e in enumerate(batch, 1):
            print(f"[{i}/{len(batch)}] {e.sender_name or e.sender}  <{e.sender}>")
            print(f"    {e.subject[:90]}")
            print(f"    {e.snippet[:90]}")
            choice = input("    correct category > ").strip().lower()
            if choice == "q":
                break
            if choice == "s" or not choice:
                continue
            if choice.isdigit() and 1 <= int(choice) <= len(_CATS):
                slug = _CATS[int(choice) - 1]
            else:
                slug = choice
            if slug not in _CATS:
                print("    (unrecognised, skipped)\n")
                continue
            labels[e.message_id] = slug
            _save_labels(labels)
            print()
    print(f"Saved {len(labels)} labels total.")


def score() -> None:
    labels = _load_labels()
    if not labels:
        print("No labels yet. Run the script without --score first.")
        return
    with SessionLocal() as db:
        rows = {e.message_id: e for e in db.query(Email).all()}
    total = correct = 0
    ml_total = ml_correct = 0
    skipped = 0
    per: dict[str, dict[str, int]] = {}
    for mid, truth in labels.items():
        e = rows.get(mid)
        if e is None:
            continue
        if e.category_source == "correction":
            # You corrected this one after labelling it, so it's no longer a fair
            # test of the model (it would be trivially "right"). Keep the held-out
            # set honest by excluding it.
            skipped += 1
            continue
        total += 1
        hit = e.category == truth
        correct += hit
        bucket = per.setdefault(truth, {"correct": 0, "total": 0})
        bucket["total"] += 1
        bucket["correct"] += int(hit)
        if e.category_source == "ml":
            ml_total += 1
            ml_correct += int(hit)

    if not total:
        print("No held-out labelled emails to score yet.")
        return
    print(f"\nHand-labelled real-inbox accuracy  ({total} held-out emails)")
    if skipped:
        print(f"  ({skipped} excluded because you corrected them after labelling)")
    print(f"  overall:            {correct}/{total} = {correct / total:.0%}")
    if ml_total:
        print(f"  model-decided only: {ml_correct}/{ml_total} = {ml_correct / ml_total:.0%}")
    margin = int(100 * (1.96 * (0.25 / total) ** 0.5)) if total else 0
    print(f"  rough 95% margin:   +/- {margin}%  (bigger sample = tighter)")
    print("\n  per category (correct/total):")
    for slug in _CATS:
        b = per.get(slug)
        if b:
            print(f"    {slug:12} {b['correct']}/{b['total']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure accuracy on a hand-labelled real sample.")
    parser.add_argument("--count", type=int, default=40, help="How many emails to label this run.")
    parser.add_argument("--score", action="store_true", help="Skip labelling, just show results.")
    args = parser.parse_args()
    if not args.score:
        label(args.count)
    score()


if __name__ == "__main__":
    main()
