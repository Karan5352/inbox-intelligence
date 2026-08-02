"""Email source abstraction - one protocol, many backends (demo, Gmail, ...)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass
class RawEmail:
    """Provider-agnostic email as pulled from a source, before categorization."""

    message_id: str
    sender: str
    sender_name: str
    subject: str
    body: str
    received_at: datetime
    recipient: str = ""
    headers: dict = field(default_factory=dict)
    snippet: str = ""
    is_read: bool = False
    # Only populated by the synthetic source; used for benchmarking, never shown as truth.
    true_category: str | None = None


class EmailSource(Protocol):
    """Anything that can yield a batch of RawEmail (demo generator, Gmail IMAP, ...)."""

    def fetch(self, limit: int) -> list[RawEmail]: ...
