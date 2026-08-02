"""Optional read-only Gmail source (IMAP + app password).

Privacy posture:
  * Only used when ``DEMO_MODE=false`` AND credentials are explicitly provided.
  * Read-only: it fetches headers/body and never deletes, moves, or marks mail.
  * Credentials come from the environment (never committed); see docs/PRIVACY.md.

Uses a Gmail App Password (Google Account → Security → App passwords), not your
real password, so the token is revocable and scope-limited.
"""

from __future__ import annotations

import contextlib
import email
import imaplib
from datetime import UTC, datetime
from email.header import decode_header
from email.message import Message
from email.utils import parseaddr, parsedate_to_datetime

from app.ingest.base import RawEmail

IMAP_HOST = "imap.gmail.com"


class GmailConfigError(RuntimeError):
    pass


def _decode(value: str | None) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            out.append(text.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def _extract_body(msg: Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(
                part.get("Content-Disposition", "")
            ):
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        return ""
    payload = msg.get_payload(decode=True)
    if isinstance(payload, bytes):
        return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return str(msg.get_payload())


class GmailSource:
    """EmailSource that pulls recent messages from Gmail over IMAP (read-only)."""

    def __init__(self, address: str | None, app_password: str | None) -> None:
        if not address or not app_password:
            raise GmailConfigError(
                "Gmail address and app password are required (set GMAIL_ADDRESS / "
                "GMAIL_APP_PASSWORD, and DEMO_MODE=false)."
            )
        self.address = address.strip()
        # Google shows app passwords as "xxxx xxxx xxxx xxxx"; the spaces are only
        # for display and IMAP login rejects them, so strip all whitespace.
        self.app_password = "".join(app_password.split())

    def fetch(self, limit: int) -> list[RawEmail]:
        conn = imaplib.IMAP4_SSL(IMAP_HOST)
        try:
            conn.login(self.address, self.app_password)
            conn.select("INBOX", readonly=True)  # readonly guarantees no flag changes
            _, data = conn.search(None, "ALL")
            ids = data[0].split()[-limit:] if data and data[0] else []
            emails: list[RawEmail] = []
            for raw_id in reversed(ids):
                _, msg_data = conn.fetch(raw_id, "(RFC822)")
                if not msg_data or not isinstance(msg_data[0], tuple):
                    continue
                emails.append(self._parse(msg_data[0][1]))
            return emails
        finally:
            with contextlib.suppress(Exception):
                conn.close()
            conn.logout()

    def _parse(self, raw_bytes: bytes) -> RawEmail:
        msg = email.message_from_bytes(raw_bytes)
        sender_name, sender_addr = parseaddr(msg.get("From", ""))
        try:
            received = parsedate_to_datetime(msg.get("Date", "")) or datetime.now(UTC)
        except (TypeError, ValueError):
            received = datetime.now(UTC)
        if received.tzinfo is None:
            received = received.replace(tzinfo=UTC)

        body = _extract_body(msg)
        headers = {k: v for k, v in msg.items() if k in {"List-Unsubscribe", "Content-Type"}}
        return RawEmail(
            message_id=msg.get("Message-ID") or f"gmail-{received.timestamp()}",
            sender=sender_addr,
            sender_name=_decode(sender_name),
            recipient=self.address,
            subject=_decode(msg.get("Subject")),
            body=body,
            headers=headers,
            snippet=body[:140],
            received_at=received,
        )
