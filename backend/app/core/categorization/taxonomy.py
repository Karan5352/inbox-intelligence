"""Canonical category taxonomy - the single source of truth for labels.

Every layer (rules, ML classifier, API, frontend) references these slugs so the
system never disagrees with itself about what a category *is*.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    slug: str
    name: str
    color: str  # hex, used by the frontend chips/charts
    icon: str  # lucide-react icon name
    description: str


# Ordered for stable display. ``uncategorized`` is the fallback and is never a
# training target - it only appears when nothing else is confident.
CATEGORIES: tuple[Category, ...] = (
    Category("work", "Work", "#2563eb", "briefcase", "Colleagues, projects, meetings, HR."),
    Category("finance", "Finance", "#059669", "banknote", "Banks, invoices, payments, receipts."),
    Category("shipping", "Shipping", "#d97706", "package", "Orders, tracking, deliveries."),
    Category("travel", "Travel", "#0891b2", "plane", "Flights, hotels, itineraries, bookings."),
    Category("promotions", "Promotions", "#db2777", "tag", "Sales, discounts, marketing offers."),
    Category("social", "Social", "#7c3aed", "users", "Social networks, connection requests."),
    Category(
        "newsletters", "Newsletters", "#4f46e5", "newspaper", "Subscriptions, digests, blogs."
    ),
    Category("updates", "Updates", "#0d9488", "bell", "Account notices, service notifications."),
    Category("support", "Support", "#dc2626", "life-buoy", "Help desk, tickets, customer service."),
    Category("events", "Events", "#ca8a04", "calendar", "Invites, RSVPs, calendar items."),
    Category(
        "personal", "Personal", "#e11d48", "heart", "Friends, family, personal correspondence."
    ),
    Category("spam", "Spam", "#6b7280", "shield-alert", "Unsolicited or suspicious mail."),
    Category("uncategorized", "Uncategorized", "#94a3b8", "help-circle", "No confident match."),
)

BY_SLUG: dict[str, Category] = {c.slug: c for c in CATEGORIES}

# Categories the ML classifier is allowed to predict (everything real, minus the
# uncategorized fallback which is a confidence artifact, not a learned class).
TRAINABLE_SLUGS: tuple[str, ...] = tuple(c.slug for c in CATEGORIES if c.slug != "uncategorized")

FALLBACK_SLUG = "uncategorized"


def is_valid(slug: str) -> bool:
    return slug in BY_SLUG


def get(slug: str) -> Category:
    return BY_SLUG[slug]
