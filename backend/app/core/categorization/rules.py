"""Deterministic rule stage.

These run before the ML model. They are cheap, precise on the obvious cases, and
easy to explain, so the UI can show a concrete reason ("from ups.com, a known
carrier") rather than a bare model score. When several signals agree on the same
category we bump the confidence a little, which also keeps scores from looking
identical across a whole category.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class RuleContext:
    sender: str
    subject: str
    body: str
    headers: dict

    @property
    def domain(self) -> str:
        _, _, dom = self.sender.partition("@")
        return dom.lower()

    @property
    def text(self) -> str:
        return f"{self.subject} {self.body}".lower()


@dataclass
class RuleMatch:
    category: str
    confidence: float
    reason: str


# Sender domains we recognise. Matched on label boundaries (see _domain_matches),
# not as raw substrings, so a short domain like "x.com" never matches "dropbox.com".
_DOMAIN_MAP: dict[str, list[str]] = {
    "shipping": ["amazon.com", "ups.com", "fedex.com", "usps.com", "dhl.com", "shopify.com"],
    "finance": [
        "paypal.com",
        "chase.com",
        "bankofamerica.com",
        "wellsfargo.com",
        "stripe.com",
        "venmo.com",
        "intuit.com",
        "americanexpress.com",
    ],
    "travel": [
        "united.com",
        "delta.com",
        "aa.com",
        "airbnb.com",
        "booking.com",
        "expedia.com",
        "marriott.com",
        "hilton.com",
        "southwest.com",
    ],
    "social": [
        "linkedin.com",
        "facebook.com",
        "facebookmail.com",
        "twitter.com",
        "x.com",
        "instagram.com",
        "reddit.com",
        "tiktok.com",
    ],
}


def _domain_matches(domain: str, pattern: str) -> bool:
    """True if domain is pattern or a subdomain of it (label-boundary match)."""
    return domain == pattern or domain.endswith("." + pattern)


_SPAM_PATTERNS = [
    r"you('ve| have) won",
    r"claim (your|now)",
    r"free gift card",
    r"act now",
    r"unclaimed (inheritance|funds)",
    r"wire transfer",
    r"hot singles",
    r"viagra",
    r"risk[- ]free",
    r"congratulations.*winner",
]
_SHIPPING_KW = ["shipped", "tracking", "out for delivery", "delivered", "your order", "package"]
_FINANCE_KW = ["invoice", "payment", "statement", "receipt", "transaction", "balance due", "remit"]
_TRAVEL_KW = [
    "itinerary",
    "boarding pass",
    "reservation",
    "check-in",
    "booking confirmed",
    "flight",
]
_EVENT_KW = [
    "rsvp",
    "you're invited",
    "you are invited",
    "calendar invite",
    "webinar",
    "register now",
]
_SUPPORT_KW = ["ticket", "support request", "case #", "case number", "help desk", "resolved"]
_PROMO_KW = ["sale", "% off", "discount", "deal", "offer", "coupon", "save"]
# Strong sale signals; used against the subject line to beat footer boilerplate.
_STRONG_PROMO = [
    "% off",
    "off all",
    "bogo",
    "buy one",
    "clearance",
    "today only",
    "flash sale",
    "on sale",
    "$ off",
    "% back",
    "markdown",
    "ends tonight",
    "limited time",
]
_SOCIAL_KW = [
    "connection request",
    "tagged you",
    "friend request",
    "started following",
    "mentioned you",
    "new notifications",
    "new followers",
    "invitation to connect",
]

# Unambiguous account-notice phrases. These are specific enough to trust over the
# model (unlike "verify your account", which phishing also uses, so it is left out).
_UPDATES_KW = [
    "security alert",
    "new sign-in",
    "terms of service",
    "privacy policy",
    "subscription will renew",
    "password was changed",
]


def _has_unsubscribe(ctx: RuleContext) -> bool:
    return any(k.lower() == "list-unsubscribe" for k in ctx.headers)


def _is_no_reply(ctx: RuleContext) -> bool:
    local = ctx.sender.split("@", 1)[0].lower()
    return "no-reply" in local or "noreply" in local or "donotreply" in local


def _any(text: str, needles: list[str]) -> bool:
    return any(n in text for n in needles)


def evaluate(ctx: RuleContext) -> RuleMatch | None:
    """Return the strongest rule match, or None when nothing fires.

    When more than one signal points at the same category, the extra agreement
    nudges the score up, so a domain hit that is also backed by keywords reads
    higher than a domain hit alone.
    """
    matches: list[RuleMatch] = []
    subject = ctx.subject.lower()

    # Known sender domains are the most reliable signal we have.
    for category, domains in _DOMAIN_MAP.items():
        if any(_domain_matches(ctx.domain, d) for d in domains):
            src = ctx.domain or "this sender"
            matches.append(RuleMatch(category, 0.9, f"From {src}, a known {category} sender"))

    # Calendar attachments are unambiguous.
    if (
        ctx.headers.get("Content-Type", "").startswith("text/calendar")
        or "begin:vcalendar" in ctx.body.lower()
    ):
        matches.append(RuleMatch("events", 0.9, "Carries a calendar invitation"))

    # Spam: needs either two hits or one hit plus shouty punctuation.
    spam_hits = sum(bool(re.search(p, ctx.text)) for p in _SPAM_PATTERNS)
    if spam_hits >= 1 and (ctx.text.count("!") >= 3 or spam_hits >= 2):
        matches.append(RuleMatch("spam", 0.86, "Reads like a scam or bulk spam"))

    # Content keywords. Weaker on their own, but they corroborate a domain hit.
    if _any(ctx.text, _SHIPPING_KW):
        matches.append(RuleMatch("shipping", 0.8, "Talks about an order or delivery"))
    if _any(ctx.text, _FINANCE_KW):
        matches.append(RuleMatch("finance", 0.8, "Mentions an invoice, payment, or statement"))
    if _any(ctx.text, _TRAVEL_KW):
        matches.append(RuleMatch("travel", 0.8, "Looks like a booking or itinerary"))
    if _any(ctx.text, _EVENT_KW):
        matches.append(RuleMatch("events", 0.8, "Has an invitation or RSVP"))
    if _any(ctx.text, _SUPPORT_KW):
        matches.append(RuleMatch("support", 0.8, "References a support ticket or case"))
    if _any(ctx.text, _SOCIAL_KW):
        # These phrases ("mentioned you", "tagged you", ...) are unambiguously social,
        # so trust them over the model, which otherwise scatters them into support etc.
        matches.append(RuleMatch("social", 0.86, "A social network notification"))
    # Account-notice keywords are matched against the SUBJECT only. In the body they
    # are footer boilerplate ("privacy policy", "terms of service") present in almost
    # every marketing email, which was misfiling promotions as updates.
    if _any(subject, _UPDATES_KW):
        matches.append(RuleMatch("updates", 0.88, "An account or security notice"))

    # Strong sale language in the subject means promotions, even without an
    # unsubscribe header (and it should beat a footer that mentions a policy).
    if _any(subject, _STRONG_PROMO):
        matches.append(RuleMatch("promotions", 0.86, "Subject uses strong sale language"))

    # Bulk senders (unsubscribe header): promotional if salesy, else a newsletter.
    if _has_unsubscribe(ctx):
        if _any(ctx.text, _PROMO_KW):
            matches.append(RuleMatch("promotions", 0.85, "Bulk sender using sales language"))
        else:
            matches.append(RuleMatch("newsletters", 0.7, "Bulk sender with an unsubscribe link"))

    # Generic no-reply account mail (subject-based, to avoid footer boilerplate).
    if _is_no_reply(ctx) and _any(subject, ["verify", "security", "password", "renew"]):
        matches.append(RuleMatch("updates", 0.73, "Automated no-reply account mail"))

    if not matches:
        return None

    # Pick the best category, then reward agreement between separate signals.
    best = max(matches, key=lambda m: m.confidence)
    corroboration = sum(1 for m in matches if m.category == best.category) - 1
    confidence = min(0.97, best.confidence + 0.04 * corroboration)
    return RuleMatch(best.category, round(confidence, 4), best.reason)
