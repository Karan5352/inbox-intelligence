"""Pure insight heuristics (no DB), kept here so they're unit-testable."""

from __future__ import annotations

# Categories that typically expect a human response.
_ACTIONABLE = {"work", "personal", "support"}


def needs_reply(*, category: str, is_read: bool, is_archived: bool) -> bool:
    """Heuristic: unread, not archived, and in a conversational category."""
    return (not is_read) and (not is_archived) and category in _ACTIONABLE
