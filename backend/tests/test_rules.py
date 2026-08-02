"""Unit tests for the deterministic rule stage."""

from __future__ import annotations

import pytest

from app.core.categorization import rules


def ctx(sender="a@b.com", subject="", body="", headers=None):
    return rules.RuleContext(sender=sender, subject=subject, body=body, headers=headers or {})


def test_known_shipping_domain():
    m = rules.evaluate(ctx(sender="ship@amazon.com", subject="Your order", body="has shipped"))
    assert m is not None and m.category == "shipping" and m.confidence >= 0.8


def test_finance_keywords():
    m = rules.evaluate(ctx(subject="Invoice #12", body="Your payment is due, remit balance"))
    assert m is not None and m.category == "finance"


def test_unsubscribe_promotional():
    m = rules.evaluate(
        ctx(subject="40% off sale", body="huge discount deal", headers={"List-Unsubscribe": "<x>"})
    )
    assert m is not None and m.category == "promotions"


def test_unsubscribe_newsletter_when_not_salesy():
    m = rules.evaluate(
        ctx(subject="Weekly digest", body="stories to read", headers={"List-Unsubscribe": "<x>"})
    )
    assert m is not None and m.category == "newsletters"


def test_spam_heuristic():
    m = rules.evaluate(ctx(subject="You have won!!!", body="claim now!!! free gift card!!!"))
    assert m is not None and m.category == "spam"


def test_calendar_invite_is_event():
    m = rules.evaluate(ctx(body="BEGIN:VCALENDAR", subject="Invitation"))
    assert m is not None and m.category == "events"


def test_no_match_returns_none():
    assert rules.evaluate(ctx(subject="hello", body="just saying hi")) is None


def test_domain_match_respects_label_boundaries():
    # "x.com" (a social domain) must not match "dropbox.com" as a raw substring.
    m = rules.evaluate(
        ctx(
            sender="no-reply@dropbox.com",
            subject="We've updated our terms of service",
            body="review the changes to our policy",
        )
    )
    assert m is not None and m.category == "updates"  # not social
    # A real x.com sender (or subdomain) still matches social.
    assert rules.evaluate(ctx(sender="a@x.com", subject="hi")).category == "social"
    assert rules.evaluate(ctx(sender="a@mail.x.com", subject="hi")).category == "social"


@pytest.mark.parametrize("local", ["no-reply", "noreply", "donotreply"])
def test_no_reply_account_notice(local):
    m = rules.evaluate(ctx(sender=f"{local}@service.com", subject="verify your password"))
    assert m is not None and m.category == "updates"
