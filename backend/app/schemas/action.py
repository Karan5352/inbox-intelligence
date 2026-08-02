"""Bulk-action and automation DTOs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

BulkActionType = Literal[
    "archive", "unarchive", "mark_read", "mark_unread", "label", "delete", "recategorize"
]


class BulkActionIn(BaseModel):
    action: BulkActionType
    email_ids: list[int] = Field(default_factory=list)
    # Optional filter form: apply to every email in a category instead of an id list.
    category: str | None = None
    value: str | None = Field(
        default=None, description="Label to add, or target category for recategorize"
    )
    dry_run: bool = Field(default=True, description="Preview only; do not mutate. Safe default.")


class BulkActionResult(BaseModel):
    action: str
    dry_run: bool
    affected: int
    email_ids: list[int]
    message: str


# --- Automations ---
class AutomationCondition(BaseModel):
    field: Literal["category", "sender", "subject", "unread"]
    op: Literal["equals", "contains", "is_true"]
    value: str = ""


class AutomationAction(BaseModel):
    type: Literal["label", "archive", "mark_read", "recategorize"]
    value: str = ""


class AutomationIn(BaseModel):
    name: str
    enabled: bool = True
    priority: int = 100
    condition: AutomationCondition
    action: AutomationAction


class AutomationOut(BaseModel):
    id: int
    name: str
    enabled: bool
    priority: int
    condition: AutomationCondition
    action: AutomationAction
    run_count: int
    created_at: datetime


class AutomationRunResult(BaseModel):
    dry_run: bool
    matched: int
    applied: int
    by_automation: dict[str, int]
