"""Pure evaluation of an automation condition against an email-like mapping.

Conditions are plain data so the whole rule set is inspectable and testable:
    {"field": "category", "op": "equals", "value": "promotions"}
"""

from __future__ import annotations

from typing import Any


def matches(condition: dict[str, Any], email: dict[str, Any]) -> bool:
    field = str(condition.get("field", ""))
    op = condition.get("op")
    value = str(condition.get("value", "")).lower()

    if field == "unread":
        return op == "is_true" and not email.get("is_read", False)

    haystack = str(email.get(field, "")).lower()
    if op == "equals":
        return haystack == value
    if op == "contains":
        return value in haystack
    return False
