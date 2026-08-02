"""Email ORM model - one row per ingested message (synthetic or real)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Email(Base, TimestampMixin):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Stable id from the source (synthetic uuid or Gmail Message-ID). Dedupe key.
    message_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    sender: Mapped[str] = mapped_column(String(320), index=True)  # email address
    sender_name: Mapped[str] = mapped_column(String(255), default="")
    recipient: Mapped[str] = mapped_column(String(320), default="")
    subject: Mapped[str] = mapped_column(String(1000), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    snippet: Mapped[str] = mapped_column(String(300), default="")
    # Raw header hints used by the rules engine (e.g. List-Unsubscribe presence).
    headers: Mapped[dict] = mapped_column(JSON, default=dict)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    labels: Mapped[list] = mapped_column(JSON, default=list)  # automation-applied labels

    # --- Categorization result ---
    category: Mapped[str] = mapped_column(String(40), default="uncategorized", index=True)
    category_source: Mapped[str] = mapped_column(String(20), default="ml")  # rule|ml|correction
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str] = mapped_column(String(500), default="")
    # Other categories that scored close to the primary. Display only; the primary
    # category above is still the single label used everywhere else.
    secondary: Mapped[list] = mapped_column(JSON, default=list)

    # The ground-truth label the synthetic generator assigned. Used ONLY for
    # benchmarking (never shown as truth to the classifier at inference time).
    true_category: Mapped[str | None] = mapped_column(String(40), nullable=True)

    def content(self) -> str:
        """Text fed to the categorizer: subject carries the most signal, so weight it."""
        return f"{self.subject}\n{self.subject}\n{self.body}".strip()
