"""Metric ORM model - accuracy snapshots powering the 'learns from you' story.

A row is written whenever we evaluate the classifier on the held-out set (e.g.
before and after applying corrections), so the Insights page can plot a real
learning curve rather than a claimed one.
"""

from __future__ import annotations

from sqlalchemy import JSON, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Metric(Base, TimestampMixin):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(60), index=True)  # e.g. "baseline", "correction"
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    macro_f1: Mapped[float] = mapped_column(Float, default=0.0)
    num_corrections: Mapped[int] = mapped_column(Integer, default=0)
    num_examples: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)  # per-category breakdown
