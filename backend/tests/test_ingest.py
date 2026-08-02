"""Tests for the ingest layer: demo generator, Gmail parsing, sync endpoint."""

from __future__ import annotations

from email.message import EmailMessage

from fastapi.testclient import TestClient

from app.ingest.demo import generate
from app.ingest.gmail import GmailConfigError, GmailSource


def test_demo_generator_is_deterministic():
    a = generate(count=30, seed=1)
    b = generate(count=30, seed=1)
    assert [e.message_id for e in a] == [e.message_id for e in b]
    assert all(e.true_category for e in a)


def test_gmail_requires_credentials():
    try:
        GmailSource(None, None)
    except GmailConfigError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected GmailConfigError")


def test_gmail_parse_message():
    msg = EmailMessage()
    msg["From"] = "Jane Doe <jane@example.com>"
    msg["Subject"] = "Hello there"
    msg["Date"] = "Wed, 02 Jul 2025 10:00:00 +0000"
    msg["Message-ID"] = "<abc@example.com>"
    msg.set_content("This is the body text.")

    source = GmailSource("me@gmail.com", "app-pass")
    parsed = source._parse(msg.as_bytes())
    assert parsed.sender == "jane@example.com"
    assert parsed.sender_name == "Jane Doe"
    assert parsed.subject == "Hello there"
    assert "body text" in parsed.body
    assert parsed.received_at.tzinfo is not None


def test_sync_endpoint_uses_demo_in_demo_mode(client: TestClient):
    res = client.post("/sync?limit=20").json()
    assert res["source"] == "demo"
    assert res["added"] == 20
    assert client.get("/emails").json()["total"] >= 20
