"""Tests for email body cleaning."""

from __future__ import annotations

from app.core.text import clean_email_text


def test_strips_html():
    out = clean_email_text("<p>Hello <b>there</b></p><style>.x{color:red}</style>")
    assert "Hello" in out and "there" in out
    assert "<" not in out and "color:red" not in out


def test_unescapes_entities():
    assert "AT&T" in clean_email_text("<div>AT&amp;T account</div>")


def test_drops_quoted_reply_thread():
    body = "My actual reply.\n\nOn Mon, Jan 1, 2026, Jane wrote:\n> old message\n> more quoted"
    out = clean_email_text(body)
    assert "My actual reply." in out
    assert "old message" not in out


def test_drops_quoted_lines_and_signature():
    body = "Real content here.\n> quoted line\n-- \nSent from my phone"
    out = clean_email_text(body)
    assert "Real content here." in out
    assert "quoted line" not in out
    assert "Sent from my phone" not in out


def test_plain_text_passes_through():
    body = "Your order has shipped and is out for delivery."
    assert clean_email_text(body) == body


def test_truncates_long_bodies():
    assert len(clean_email_text("word " * 2000)) <= 2000
