"""Synthetic email generator for demo mode.

Everything the app shows by default comes from here, so it can be run and shown
publicly without touching a real inbox. Generation is seeded, so the same call
gives back the same inbox and the benchmark stays reproducible.

Each email keeps a ``true_category`` that only the benchmark reads. Templates use
short placeholders (order numbers, names, amounts) that get filled per message so
two emails from the same template still look different, and each category mixes
well-known senders (which the rules catch) with lesser-known ones (which fall
through to the model), so categories, sources, and confidences vary the way a
real inbox does.
"""

from __future__ import annotations

import random
import re
from datetime import UTC, datetime, timedelta

from app.ingest.base import RawEmail

_NAMES = [
    "Alex",
    "Sam",
    "Priya",
    "Marcus",
    "Jordan",
    "Lena",
    "Diego",
    "Mei",
    "Noah",
    "Ava",
    "Ravi",
    "Chloe",
    "Tom",
    "Nadia",
    "Owen",
]
_CITIES = ["Austin", "Denver", "Seattle", "Chicago", "Boston", "Portland", "Miami", "Toronto"]
_COMPANIES = ["Northwind", "Contoso", "Globex", "Meridian", "Lumen", "Riverstone", "Blue Harbor"]
_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# (sender_name, sender_addr, subject, body, headers, true_category)
_TEMPLATES: list[tuple[str, str, str, str, dict, str]] = [
    # work
    (
        "{name} Okafor",
        "{name2}@meridian.io",
        "Re: Q3 roadmap review",
        "Can we grab 30 minutes {day} to walk through the roadmap before the leadership sync? "
        "I left a few comments in the doc.",
        {},
        "work",
    ),
    (
        "{name} Park",
        "{name2}@lumen.co",
        "Notes from today's standup",
        "Quick recap: we closed {n} tickets, the migration slipped a day, and design signs off {day}.",
        {},
        "work",
    ),
    (
        "People Ops",
        "people@northwind.com",
        "Reminder: submit your timesheet",
        "Friendly reminder to submit your timesheet before end of day {day}.",
        {},
        "work",
    ),
    (
        "{name} Alvarez",
        "{name2}@contoso.com",
        "Draft ready for your review",
        "The proposal draft is ready whenever you have a moment. No rush, but I'd like to send it {day}.",
        {},
        "work",
    ),
    (
        "Recruiting",
        "talent@globex.com",
        "Interview debrief for the backend role",
        "Thanks for interviewing {name3}. Could you drop your feedback in the tracker by {day}?",
        {},
        "work",
    ),
    (
        "{name} Boyd",
        "{name2}@riverstone.dev",
        "Can you review PR #{n}{n}",
        "When you get a chance, mind reviewing the auth change? It's small, mostly moving code around.",
        {},
        "work",
    ),
    # finance
    (
        "Chase",
        "no-reply@chase.com",
        "Your statement is ready",
        "Your monthly statement is available. Current balance is ${amount}.",
        {"List-Unsubscribe": "<mailto:u@chase.com>"},
        "finance",
    ),
    (
        "PayPal",
        "service@paypal.com",
        "You sent a payment of ${amount}",
        "You sent ${amount} to {name3}. Transaction id {code}.",
        {},
        "finance",
    ),
    (
        "Stripe",
        "receipts@stripe.com",
        "Receipt from {company} [#{order}]",
        "Thanks for your payment. Invoice #{order} for ${amount} has been paid.",
        {},
        "finance",
    ),
    (
        "{name} at Ledgerly",
        "billing@ledgerly.app",
        "Invoice #{order} is due {day}",
        "Your invoice for ${amount} is due {day}. Please remit payment at your convenience.",
        {},
        "finance",
    ),
    (
        "Venmo",
        "venmo@venmo.com",
        "{name3} paid you ${amount}",
        "{name3} sent you ${amount}. The money is in your Venmo balance.",
        {},
        "finance",
    ),
    (
        "Rentwell",
        "payments@rentwell.co",
        "Rent receipt for this month",
        "We received your rent payment of ${amount}. Transaction {code}. Thanks!",
        {},
        "finance",
    ),
    # shipping
    (
        "Amazon",
        "ship-confirm@amazon.com",
        "Your order has shipped",
        "Your order of a USB-C cable has shipped and is out for delivery. Tracking {code}.",
        {},
        "shipping",
    ),
    (
        "UPS",
        "no-reply@ups.com",
        "Your package is on the way",
        "Your parcel is in transit. Estimated delivery {day} by 8 PM. Tracking {code}.",
        {},
        "shipping",
    ),
    (
        "USPS",
        "no-reply@usps.com",
        "Delivered: your package arrived",
        "Your package was delivered to the front door. Reference {code}.",
        {},
        "shipping",
    ),
    (
        "{company} Store",
        "orders@{company2}.shop",
        "Order #{order} confirmed",
        "Thanks for your order. We're packing it now and will email tracking once it ships.",
        {},
        "shipping",
    ),
    (
        "Etsy Seller",
        "hello@craftnest.store",
        "Your handmade order shipped",
        "Good news, your order is on its way. Delivery expected around {day}.",
        {},
        "shipping",
    ),
    (
        "FedEx",
        "tracking@fedex.com",
        "Out for delivery today",
        "Your shipment {code} is out for delivery and should arrive by end of day.",
        {},
        "shipping",
    ),
    # travel
    (
        "Delta Air Lines",
        "confirmation@delta.com",
        "Your flight is confirmed",
        "Your itinerary is confirmed. Departure 6:45 AM from gate B12. Check-in opens 24 hours prior.",
        {},
        "travel",
    ),
    (
        "Airbnb",
        "automated@airbnb.com",
        "Reservation confirmed in {city}",
        "Your booking is confirmed for two nights in {city}. Your host will send check-in details soon.",
        {},
        "travel",
    ),
    (
        "Booking.com",
        "no-reply@booking.com",
        "Your hotel booking is set",
        "Reservation confirmed at a hotel in {city}. Free cancellation until the day before check-in.",
        {},
        "travel",
    ),
    (
        "Seaside Inn",
        "stay@seasideinn.co",
        "Your reservation details",
        "We look forward to hosting you in {city}. Check-in is at 3 PM {day}. Booking confirmed.",
        {},
        "travel",
    ),
    (
        "TripPlanner",
        "hello@tripplanner.io",
        "Your {city} itinerary",
        "Here is your itinerary for {city}: flight, hotel, and two dinner reservations. Safe travels!",
        {},
        "travel",
    ),
    (
        "Southwest",
        "noreply@southwest.com",
        "Check-in is now open",
        "Check-in is open for your upcoming flight. Boarding pass attached.",
        {},
        "travel",
    ),
    # promotions
    (
        "Nike",
        "news@nike.com",
        "40% off everything this weekend",
        "Take 40% off sitewide with code SAVE40. This deal ends {day}, so don't wait.",
        {"List-Unsubscribe": "<mailto:u@nike.com>"},
        "promotions",
    ),
    (
        "Best Buy",
        "deals@emailinfo.bestbuy.com",
        "A coupon just for you",
        "Enjoy an extra 20% off. Limited-time offer, discount ends {day}.",
        {"List-Unsubscribe": "<mailto:u@bestbuy.com>"},
        "promotions",
    ),
    (
        "DoorDash",
        "no-reply@doordash.com",
        "Half off your next {n} orders",
        "Enjoy 50% off your next {n} orders with code EAT50. Offer ends soon.",
        {"List-Unsubscribe": "<mailto:u@doordash.com>"},
        "promotions",
    ),
    (
        "Brew & Co",
        "hello@brewandco.coffee",
        "Your favorite beans are on sale",
        "This week only, save 25% on our house blend. Use code MORNING at checkout.",
        {"List-Unsubscribe": "<mailto:u@brewandco.coffee>"},
        "promotions",
    ),
    (
        "Fitwear",
        "offers@fitwear.shop",
        "Last chance, deal ends {day}",
        "Your cart is waiting and prices drop tonight. Grab the sale before it's gone.",
        {"List-Unsubscribe": "<mailto:u@fitwear.shop>"},
        "promotions",
    ),
    # social
    (
        "LinkedIn",
        "notifications@linkedin.com",
        "You have {n} new connection requests",
        "You have {n} pending invitations waiting for a response.",
        {"List-Unsubscribe": "<mailto:u@linkedin.com>"},
        "social",
    ),
    (
        "Instagram",
        "no-reply@instagram.com",
        "{name3} tagged you in a photo",
        "{name3} tagged you in a new photo. See it now.",
        {"List-Unsubscribe": "<mailto:u@instagram.com>"},
        "social",
    ),
    (
        "Facebook",
        "notification@facebookmail.com",
        "You have new notifications",
        "You have {n} new notifications and {n} friend requests waiting.",
        {"List-Unsubscribe": "<mailto:u@facebookmail.com>"},
        "social",
    ),
    (
        "Threadly",
        "hi@threadly.social",
        "{name3} started following you",
        "{name3} and {n} others started following you this week.",
        {"List-Unsubscribe": "<mailto:u@threadly.social>"},
        "social",
    ),
    (
        "Discord",
        "no-reply@discord.com",
        "{name3} mentioned you",
        "You were mentioned in the {company} server. Jump back in to catch up.",
        {},
        "social",
    ),
    # newsletters
    (
        "Morning Brew",
        "crew@morningbrew.com",
        "This week in business and tech",
        "The five stories worth reading this morning, plus a look at markets and one long read.",
        {"List-Unsubscribe": "<mailto:u@morningbrew.com>"},
        "newsletters",
    ),
    (
        "The Pragmatic Engineer",
        "hi@pragmaticengineer.com",
        "Issue #{order}: scaling teams",
        "This week: how fast-growing companies structure engineering teams, plus links and long reads.",
        {"List-Unsubscribe": "<mailto:u@pragmaticengineer.com>"},
        "newsletters",
    ),
    (
        "GitHub",
        "digest@github.com",
        "Your weekly activity digest",
        "Here's what happened across your repos this week: {n} new stars and {n} pull requests.",
        {"List-Unsubscribe": "<mailto:u@github.com>"},
        "newsletters",
    ),
    (
        "{name}'s Substack",
        "{name2}@substack.com",
        "On building small things",
        "A short note this week about shipping side projects and why constraints help.",
        {"List-Unsubscribe": "<mailto:u@substack.com>"},
        "newsletters",
    ),
    (
        "Dense Discovery",
        "hello@densediscovery.com",
        "Issue {order}",
        "This week's tools, reads, and one idea to sit with over the weekend.",
        {"List-Unsubscribe": "<mailto:u@densediscovery.com>"},
        "newsletters",
    ),
    # updates
    (
        "Google",
        "no-reply@accounts.google.com",
        "Security alert: new sign-in",
        "We detected a new sign-in on a Mac. If this was you, no action is needed. Otherwise verify "
        "your account and change your password.",
        {},
        "updates",
    ),
    (
        "Dropbox",
        "no-reply@dropbox.com",
        "We've updated our terms of service",
        "We're updating our terms of service next month. Please review the changes to our policy.",
        {},
        "updates",
    ),
    (
        "Spotify",
        "no-reply@spotify.com",
        "Your subscription will renew soon",
        "Your Premium subscription will renew automatically on the 1st. No action needed.",
        {},
        "updates",
    ),
    (
        "{company} Cloud",
        "alerts@{company2}.cloud",
        "Scheduled maintenance {day}",
        "We have scheduled maintenance {day} from 2 to 4 AM. Brief downtime is expected.",
        {},
        "updates",
    ),
    (
        "Notion",
        "team@makenotion.com",
        "New sign-in to your workspace",
        "A new device signed in to your workspace. Review recent activity if this wasn't you.",
        {},
        "updates",
    ),
    # support
    (
        "Zendesk",
        "support@help.{company2}.com",
        "[Ticket #{order}] We're looking into it",
        "Thanks for reaching out. Your support ticket #{order} has been updated and an agent is on it.",
        {},
        "support",
    ),
    (
        "Apple Support",
        "no-reply@apple.com",
        "Your case has been resolved",
        "Your support case #{order} has been resolved. Was this helpful? Let us know.",
        {},
        "support",
    ),
    (
        "Helpdesk",
        "help@{company2}.io",
        "Re: your help request",
        "Sorry you hit a snag. Here's how to fix the sync issue you reported, step by step.",
        {},
        "support",
    ),
    (
        "{company} Billing",
        "care@{company2}.co",
        "We refunded your last charge",
        "Following up on case #{order}, we've issued a refund of ${amount}. It should post in a few days.",
        {},
        "support",
    ),
    # events
    (
        "Eventbrite",
        "no-reply@eventbrite.com",
        "You're invited: launch party",
        "You're invited. RSVP for the launch party {day} at 6 PM. Space is limited, so register now.",
        {},
        "events",
    ),
    (
        "Calendar",
        "calendar-notification@google.com",
        "Invitation: Team offsite {day}",
        "You've been invited to the team offsite on {day}. Please RSVP.",
        {"Content-Type": "text/calendar; method=REQUEST"},
        "events",
    ),
    (
        "Meetup",
        "info@meetup.com",
        "Reminder: your event starts in an hour",
        "The {city} developers meetup starts in one hour. See you there.",
        {"List-Unsubscribe": "<mailto:u@meetup.com>"},
        "events",
    ),
    (
        "{name} Reyes",
        "{name2}@gmail.com",
        "Dinner party {day}?",
        "Throwing a small dinner {day} and would love for you to come. Let me know if you can make it.",
        {},
        "events",
    ),
    (
        "Luma",
        "hello@lu.ma",
        "You're going: {city} founders night",
        "You're confirmed for founders night in {city}. Doors open at 7. Bring a friend.",
        {},
        "events",
    ),
    # personal
    (
        "{name} Rivera",
        "{name2}@gmail.com",
        "Dinner this weekend?",
        "Are we still on for dinner Saturday? Let me know what time works and I'll book a table.",
        {},
        "personal",
    ),
    (
        "Mom",
        "linda.family@gmail.com",
        "Photos from the trip",
        "Can you send me those photos from the trip when you get a chance? Love you.",
        {},
        "personal",
    ),
    (
        "{name} Kim",
        "{name2}@gmail.com",
        "Thank you",
        "Thanks so much for the birthday wishes yesterday, it meant a lot. Let's catch up soon.",
        {},
        "personal",
    ),
    (
        "{name} Osei",
        "{name2}@outlook.com",
        "Long time no talk",
        "Was just thinking about you. How have you been? We should grab coffee when you're free.",
        {},
        "personal",
    ),
    (
        "{name} Bianchi",
        "{name2}@icloud.com",
        "That book I mentioned",
        "Finally remembered the title of the book I told you about. Sending it over, you'll like it.",
        {},
        "personal",
    ),
    # spam
    (
        "Prize Center",
        "winner@lucky-prizes-intl.biz",
        "CONGRATULATIONS you have WON",
        "You have won a ${amount}00 gift card. Claim your prize now before it expires. Act now!",
        {},
        "spam",
    ),
    (
        "Account Security",
        "verify@secure-alert.info",
        "Urgent: verify your account now",
        "Your account will be closed unless you verify immediately. Claim now to avoid suspension!",
        {},
        "spam",
    ),
    (
        "Transfer Dept",
        "agent@intl-transfer.biz",
        "You have an unclaimed inheritance",
        "You have an unclaimed inheritance of several million waiting. Reply with your bank details to "
        "claim your funds.",
        {},
        "spam",
    ),
    (
        "Rewards Team",
        "rewards@you-won-today.biz",
        "Final notice about your reward",
        "This is your final notice. Claim your free gift card now, act now before it is gone!",
        {},
        "spam",
    ),
]

_TOKEN_RE = re.compile(r"\{(\w+)\}")


def _fill(text: str, rng: random.Random) -> str:
    """Replace {tokens} with per-message values so repeats still differ."""

    def value(key: str) -> str:
        if key == "name":
            return rng.choice(_NAMES)
        if key == "name2":
            return rng.choice(_NAMES).lower() + str(rng.randint(1, 99))
        if key == "name3":
            return rng.choice(_NAMES)
        if key == "city":
            return rng.choice(_CITIES)
        if key == "company":
            return rng.choice(_COMPANIES)
        if key == "company2":
            return rng.choice(_COMPANIES).lower().replace(" ", "")
        if key == "day":
            return rng.choice(_WEEKDAYS)
        if key == "order":
            return str(rng.randint(1000, 9999))
        if key == "amount":
            return f"{rng.randint(8, 480)}.{rng.randint(0, 99):02d}"
        if key == "code":
            return "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ0123456789") for _ in range(8))
        if key == "n":
            return str(rng.randint(2, 9))
        return key

    return _TOKEN_RE.sub(lambda m: value(m.group(1)), text)


def generate(count: int = 240, *, seed: int = 42) -> list[RawEmail]:
    """Build ``count`` synthetic emails by sampling and filling in templates."""
    rng = random.Random(seed)
    base = datetime.now(UTC)
    emails: list[RawEmail] = []
    for i in range(count):
        name, addr, subject, body, headers, category = rng.choice(_TEMPLATES)
        name = _fill(name, rng)
        addr = _fill(addr, rng)
        subject = _fill(subject, rng)
        body = _fill(body, rng)
        received = base - timedelta(hours=i * rng.uniform(0.5, 3.0))
        emails.append(
            RawEmail(
                message_id=f"demo-{i:04d}@inbox.local",
                sender=addr,
                sender_name=name,
                subject=subject,
                body=body,
                recipient="you@inbox.local",
                headers=dict(headers),
                snippet=body[:140],
                received_at=received,
                is_read=rng.random() < 0.4,
                true_category=category,
            )
        )
    return emails


class DemoSource:
    """EmailSource backed by the synthetic generator."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def fetch(self, limit: int) -> list[RawEmail]:
        return generate(count=limit, seed=self.seed)
