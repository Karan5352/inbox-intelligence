"""Clean raw email bodies down to the text that actually carries meaning.

Real mail is full of HTML, quoted reply chains, signatures, and unsubscribe
boilerplate. Feeding all of that to the embedder buries the signal, so we strip it
before storing and before categorizing. Demo data is already plain text, so this is
close to a no-op there.
"""

from __future__ import annotations

import re
from html import unescape

_SCRIPT_STYLE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_BREAKS = re.compile(r"(?i)<\s*(br|/p|/div|/tr|/li)\s*/?>")
_TAGS = re.compile(r"<[^>]+>")
_QUOTED_LINE = re.compile(r"(?m)^\s*>.*$")
_SIGNATURE = re.compile(r"\n-- \n")
_SPACES = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES = re.compile(r"\n\s*\n+")

# Markers that begin a quoted previous message; everything after is dropped.
_REPLY_MARKERS = [
    re.compile(r"(?im)^\s*on .{0,120}\bwrote:\s*$"),
    re.compile(r"(?im)^-{2,}\s*original message\s*-{2,}\s*$"),
    re.compile(r"(?im)^_{5,}\s*$"),
    re.compile(r"(?im)^\s*from:.*\bsent:\b"),
]

_MAX_LEN = 2000


def _strip_html(text: str) -> str:
    text = _SCRIPT_STYLE.sub(" ", text)
    text = _BREAKS.sub("\n", text)
    text = _TAGS.sub(" ", text)
    return unescape(text)


def _cut_quoted_thread(text: str) -> str:
    cut = len(text)
    for marker in _REPLY_MARKERS:
        m = marker.search(text)
        if m:
            cut = min(cut, m.start())
    return text[:cut]


def clean_email_text(body: str) -> str:
    """Return a plain-text, quote/signature-free version of an email body."""
    text = body or ""
    if "<" in text and ">" in text:
        text = _strip_html(text)
    text = _cut_quoted_thread(text)
    text = _QUOTED_LINE.sub("", text)
    text = _SIGNATURE.split(text)[0]
    text = _SPACES.sub(" ", text)
    text = _BLANK_LINES.sub("\n", text).strip()
    return text[:_MAX_LEN]
