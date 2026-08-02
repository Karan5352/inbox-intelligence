"""Correction ORM model - a user relabelling an email.

Each correction is both an audit record *and* a labeled training example that the
learning loop feeds back into the classifier.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Correction(Base, TimestampMixin):
    __tablename__ = "corrections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id", ondelete="CASCADE"), index=True)
    from_category: Mapped[str] = mapped_column(String(40))
    to_category: Mapped[str] = mapped_column(String(40), index=True)
    # Snapshot of the content at correction time, so retraining is reproducible
    # even if the email is later archived/deleted.
    content: Mapped[str] = mapped_column(String, default="")
