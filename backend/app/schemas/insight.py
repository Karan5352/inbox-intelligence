"""Insights / analytics DTOs for the dashboard."""

from __future__ import annotations

from pydantic import BaseModel


class CategoryCount(BaseModel):
    category: str
    name: str
    color: str
    count: int
    unread: int


class SenderCount(BaseModel):
    sender: str
    sender_name: str
    count: int


class VolumePoint(BaseModel):
    date: str  # YYYY-MM-DD
    count: int


class AccuracyPoint(BaseModel):
    label: str
    accuracy: float
    num_corrections: int
    created_at: str


class InsightsOut(BaseModel):
    total_emails: int
    unread: int
    archived: int
    needs_reply: int
    by_category: list[CategoryCount]
    top_senders: list[SenderCount]
    volume_by_day: list[VolumePoint]
    accuracy_trend: list[AccuracyPoint]
    rule_vs_ml: dict[str, int]
