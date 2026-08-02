"""Category + correction + insight DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CategoryOut(BaseModel):
    slug: str
    name: str
    color: str
    icon: str
    description: str
    count: int = 0
    unread: int = 0


class CorrectionIn(BaseModel):
    email_id: int
    to_category: str = Field(..., description="Target category slug")


class CorrectionOut(BaseModel):
    id: int
    email_id: int
    from_category: str
    to_category: str
    created_at: datetime


class LearningStatus(BaseModel):
    classifier_examples: int  # total reference examples the classifier matches against
    from_prototypes: int  # built-in seed phrases
    from_inbox: int  # emails auto-labelled by the rules (this inbox)
    corrections: int  # your manual corrections
    embedding_backend: str
    latest_accuracy: float | None = None
