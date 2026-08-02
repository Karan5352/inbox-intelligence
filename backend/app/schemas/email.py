"""Email DTOs returned by / accepted by the API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_id: str
    sender: str
    sender_name: str
    subject: str
    snippet: str
    received_at: datetime
    is_read: bool
    is_archived: bool
    labels: list[str]
    category: str
    category_source: str
    confidence: float
    reason: str
    secondary: list[str]


class EmailDetail(EmailOut):
    body: str


class EmailPage(BaseModel):
    items: list[EmailOut]
    total: int
    limit: int
    offset: int
