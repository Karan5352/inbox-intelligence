"""Clean before/after test of the learning loop on your real inbox.

Uses the labels you already made with `evaluate_real` as a frozen test set. The
baseline step optionally clears your existing corrections (for a true from-scratch
"before"), records the model's prediction for every labelled email, and saves them.
After you make corrections in the app and re-sort, the "after" step re-scores the
*same* emails and compares before vs after on the identical held-out set, so the
delta is genuine learning transfer, not a shifting denominator.

Usage (from backend/, venv active, real inbox + labels present):
    python -m scripts.ab_test baseline --reset   # clear corrections, lock in "before"
    # ... correct some emails in the app, then Settings -> Re-sort inbox ...
    python -m scripts.ab_test after              # compare, on the same frozen set
"""

from __future__ import annotations

import argparse
import json

from app.config import DATA_DIR
from app.db.session import SessionLocal
from app.models.correction import Correction
from app.models.email import Email
from app.services import categorization_service

LABELS_PATH = DATA_DIR / "local" / "eval_labels.json"
STATE_PATH = DATA_DIR / "local" / "ab_test.json"


def _labels() -> dict[str, str]:
    if not LABELS_PATH.exists():
        raise SystemExit("No labels yet. Run `make eval` to hand-label a sample first.")
    return json.loads(LABELS_PATH.read_text())


def baseline(reset: bool) -> None:
    labels = _labels()
    with SessionLocal() as db:
        if reset:
            n = db.query(Correction).delete()
            db.commit()
            print(f"Cleared {n} existing corrections for a from-scratch baseline.")
        # Re-fit and re-sort so every email reflects the (now correction-free) model.
        categorization_service.recategorize_all(db)
        rows = {e.message_id: e for e in db.query(Email).all()}
        test = {}
        correct = 0
        for mid, truth in labels.items():
            e = rows.get(mid)
            if e is None:
                continue
            hit = e.category == truth
            correct += hit
            test[mid] = {"truth": truth, "baseline_pred": e.category, "baseline_correct": hit}
        STATE_PATH.write_text(json.dumps({"test": test}, indent=2))
    n = len(test)
    print(f"\nBASELINE locked in: {correct}/{n} = {correct / n:.0%} on {n} held-out emails.")
    print("Now correct some emails in the app, hit Settings -> Re-sort inbox, then run:")
    print("    python -m scripts.ab_test after")


def after() -> None:
    if not STATE_PATH.exists():
        raise SystemExit("No baseline saved. Run: python -m scripts.ab_test baseline --reset")
    state = json.loads(STATE_PATH.read_text())["test"]
    with SessionLocal() as db:
        rows = {e.message_id: e for e in db.query(Email).all()}

    before = after_ = n = excluded = 0
    for mid, rec in state.items():
        e = rows.get(mid)
        if e is None:
            continue
        if e.category_source == "correction":
            # You corrected this test email, so it can't be scored fairly; drop it
            # from BOTH before and after to keep the comparison apples-to-apples.
            excluded += 1
            continue
        n += 1
        before += rec["baseline_correct"]
        after_ += e.category == rec["truth"]

    if not n:
        print("No held-out emails left to compare (you corrected them all).")
        return
    delta = (after_ - before) / n
    print(
        f"\nBefore/after on the SAME {n} held-out emails "
        f"({excluded} excluded because you corrected them):"
    )
    print(f"  before: {before}/{n} = {before / n:.0%}")
    print(f"  after:  {after_}/{n} = {after_ / n:.0%}")
    print(f"  change: {delta:+.0%}")
    print("\nThis delta is honest: same emails both times, none of them taught to the model.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean before/after test of the learning loop.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("baseline", help="Lock in the 'before' (optionally clearing corrections).")
    b.add_argument("--reset", action="store_true", help="Clear existing corrections first.")
    sub.add_parser("after", help="Compare after making corrections + re-sorting.")
    args = parser.parse_args()
    if args.cmd == "baseline":
        baseline(args.reset)
    else:
        after()


if __name__ == "__main__":
    main()
