"""Reproducible categorization benchmark.

Generates a labelled synthetic test set and scores the categorizer three ways -
rules-only, ML-only, and the hybrid engine - then simulates the learning loop to
show accuracy improving as corrections arrive. Writes a Markdown report to
``docs/RESULTS.md``.

Usage (from backend/, venv active):  python -m scripts.benchmark
"""

from __future__ import annotations

from collections import defaultdict

from app.config import BACKEND_DIR, get_settings
from app.core.categorization import rules
from app.core.categorization.engine import CategorizationEngine
from app.core.categorization.prototypes import seed_examples
from app.core.categorization.taxonomy import TRAINABLE_SLUGS
from app.ingest.demo import generate

RESULTS_PATH = BACKEND_DIR.parent / "docs" / "RESULTS.md"


def _rules_only(sender: str, subject: str, body: str, headers: dict) -> str:
    ctx = rules.RuleContext(sender=sender, subject=subject, body=body, headers=headers)
    match = rules.evaluate(ctx)
    return match.category if match else "uncategorized"


def _predict(engine: CategorizationEngine, e) -> str:  # noqa: ANN001
    return engine.categorize(
        sender=e.sender, subject=e.subject, body=e.body, headers=e.headers
    ).category


def _prf(y_true: list[str], y_pred: list[str]) -> tuple[float, dict[str, dict[str, float]]]:
    """Return overall accuracy and per-category precision/recall/F1."""
    labels = sorted(set(y_true) | set(y_pred))
    tp: dict[str, int] = defaultdict(int)
    fp: dict[str, int] = defaultdict(int)
    fn: dict[str, int] = defaultdict(int)
    correct = 0
    for t, p in zip(y_true, y_pred, strict=True):
        if t == p:
            correct += 1
            tp[t] += 1
        else:
            fp[p] += 1
            fn[t] += 1
    per: dict[str, dict[str, float]] = {}
    for label in labels:
        prec = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) else 0.0
        rec = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        per[label] = {"precision": prec, "recall": rec, "f1": f1, "support": tp[label] + fn[label]}
    return correct / len(y_true), per


def _confusion(y_true: list[str], y_pred: list[str], labels: list[str]) -> list[list[int]]:
    idx = {label: i for i, label in enumerate(labels)}
    matrix = [[0] * len(labels) for _ in labels]
    for t, p in zip(y_true, y_pred, strict=True):
        if t in idx and p in idx:
            matrix[idx[t]][idx[p]] += 1
    return matrix


# Several independent test draws so the headline number is a mean, not one lucky
# seed. Each seed is a fresh synthetic inbox the classifier has never seen.
_SEEDS = [7, 11, 23, 42, 99]


def _accuracy(engine: CategorizationEngine, test) -> float:  # noqa: ANN001
    yt = [e.true_category for e in test]
    return _prf(yt, [_predict(engine, e) for e in test])[0]


def run() -> str:
    from statistics import mean

    from app.core.categorization import embeddings

    threshold = get_settings().rule_confidence_threshold
    embedder = embeddings.backend_name()

    acc: dict[str, list[float]] = {"rules": [], "ml": [], "hybrid": []}
    for seed in _SEEDS:
        test = [e for e in generate(count=300, seed=seed) if e.true_category]
        yt = [e.true_category or "" for e in test]
        acc["rules"].append(
            _prf(yt, [_rules_only(e.sender, e.subject, e.body, e.headers) for e in test])[0]
        )
        ml_engine = CategorizationEngine(rule_threshold=1.01, k=5)
        ml_engine.ensure_seeded()
        acc["ml"].append(_accuracy(ml_engine, test))
        hybrid = CategorizationEngine(rule_threshold=threshold, k=5)
        hybrid.ensure_seeded()
        acc["hybrid"].append(_accuracy(hybrid, test))

    # Per-category metrics and confusion from the first seed (representative detail).
    test0 = [e for e in generate(count=300, seed=_SEEDS[0]) if e.true_category]
    y_true0 = [e.true_category or "" for e in test0]
    hybrid0 = CategorizationEngine(rule_threshold=threshold, k=5)
    hybrid0.ensure_seeded()
    y_hybrid0 = [_predict(hybrid0, e) for e in test0]
    _, per_hybrid = _prf(y_true0, y_hybrid0)
    labels = [s for s in TRAINABLE_SLUGS if s in set(y_true0)]
    confusion = _confusion(y_true0, y_hybrid0, labels)

    report = _render(
        n=len(test0),
        n_seeds=len(_SEEDS),
        seeds=len(seed_examples()),
        embedder=embedder,
        acc={mode: (mean(v), min(v), max(v)) for mode, v in acc.items()},
        per_hybrid=per_hybrid,
        labels=labels,
        confusion=confusion,
    )
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(report, encoding="utf-8")
    return report


def _bar(value: float, width: int = 24) -> str:
    filled = round(value * width)
    return "█" * filled + "░" * (width - filled)


def _render(**k) -> str:  # noqa: ANN003
    lines: list[str] = []
    lines.append("# Benchmark Results\n")
    lines.append("> Auto-generated by `python -m scripts.benchmark`. Reproducible: seeded.\n")
    lines.append(
        f"- Task: **single-label**, **{len(k['labels'])}-class** email classification.\n"
        f"- Data: **synthetic** labelled emails, {k['n']} per draw, "
        f"averaged over **{k['n_seeds']} held-out seeds**.\n"
        f"- Embedder: **{k['embedder']}**.\n"
        f"- Classifier seeded with {k['seeds']} prototype examples.\n"
    )
    lines.append(
        "> These numbers are on synthetic data that resembles the seed prototypes, so treat "
        "them as an internal benchmark, not real-world inbox accuracy (real mail has no ground "
        "truth to score against).\n"
    )

    lines.append("## Approach comparison (mean over seeds)\n")
    lines.append("| Approach | Accuracy | Range | |")
    lines.append("|---|---:|:--:|---|")
    for name, key in [
        ("Rules only", "rules"),
        ("Model only (embeddings)", "ml"),
        ("**Hybrid (rules + model)**", "hybrid"),
    ]:
        avg, lo, hi = k["acc"][key]
        lines.append(f"| {name} | {avg:.1%} | {lo:.0%}–{hi:.0%} | `{_bar(avg)}` |")
    lines.append("")

    lines.append("## Per-category metrics (hybrid, representative seed)\n")
    lines.append("| Category | Precision | Recall | F1 | Support |")
    lines.append("|---|---:|---:|---:|---:|")
    for label in k["labels"]:
        m = k["per_hybrid"].get(label, {"precision": 0, "recall": 0, "f1": 0, "support": 0})
        row = f"{m['precision']:.2f} | {m['recall']:.2f} | {m['f1']:.2f} | {int(m['support'])}"
        lines.append(f"| {label} | {row} |")
    lines.append("")

    lines.append("## Confusion matrix (hybrid, representative seed)\n")
    header = "| true \\ pred | " + " | ".join(k["labels"]) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(k["labels"]) + 1))
    for i, label in enumerate(k["labels"]):
        row = " | ".join(str(k["confusion"][i][j]) for j in range(len(k["labels"])))
        lines.append(f"| **{label}** | {row} |")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print(run())
