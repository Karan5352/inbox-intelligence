"""Tests for display-only secondary (close-match) categories."""

from __future__ import annotations

from app.services.categorization_service import _secondary_categories


def test_returns_close_runners_up():
    scores = {"finance": 0.5, "updates": 0.4, "work": 0.05}
    assert _secondary_categories("finance", scores) == ["updates"]  # work is too weak


def test_excludes_primary_and_fallback():
    scores = {"finance": 0.5, "uncategorized": 0.45, "finance_dup": 0.0}
    assert "finance" not in _secondary_categories("finance", scores)
    assert "uncategorized" not in _secondary_categories("finance", scores)


def test_empty_when_winner_dominates():
    assert _secondary_categories("finance", {"finance": 0.9, "work": 0.05}) == []


def test_capped_at_two():
    scores = {"a": 0.5, "b": 0.45, "c": 0.4, "d": 0.35}
    assert len(_secondary_categories("a", scores)) == 2
