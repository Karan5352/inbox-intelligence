"""Automation ORM model - an IFTTT-style workflow rule.

condition/action are stored as JSON so the rule set is data, not code:
    condition: {"field": "category"|"sender"|"subject"|"unread", "op": "...", "value": "..."}
    action:    {"type": "label"|"archive"|"mark_read"|"flag", "value": "..."}
"""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Automation(Base, TimestampMixin):
    __tablename__ = "automations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)  # lower runs first
    condition: Mapped[dict] = mapped_column(JSON, default=dict)
    action: Mapped[dict] = mapped_column(JSON, default=dict)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
