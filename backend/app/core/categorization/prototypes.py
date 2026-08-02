"""Seed examples that give the classifier a starting point.

On a fresh install there are no corrections yet, so the classifier is fitted on
these short, prototypical phrases. Corrections get appended on top, so the model
drifts toward how a given user actually sorts their mail. Keep these close to the
kind of wording that shows up in each category.
"""

from __future__ import annotations

from app.core.categorization.classifier import LabeledExample

_SEED: dict[str, list[str]] = {
    "work": [
        "Can we schedule a meeting to review the roadmap before the sync?",
        "Notes from today's standup: we closed several tickets this sprint.",
        "The proposal draft is ready for your review whenever you have time.",
        "Reminder to submit your timesheet by end of day Friday.",
        "Could you leave your interview feedback in the hiring tracker?",
        "Mind reviewing my pull request when you get a chance?",
        "Following up on the project plan and the deadline for next week.",
        "Let's align on priorities for the quarter in our one on one.",
    ],
    "finance": [
        "Your monthly statement is available and your balance is shown below.",
        "You sent a payment and here is your transaction receipt.",
        "Invoice is due soon, please remit payment at your convenience.",
        "Your card was charged and the receipt is attached.",
        "We received your rent payment for this month, thank you.",
        "A refund has been issued and should post in a few days.",
        "Your direct deposit has landed in your checking account.",
        "Payment confirmation for your recent purchase.",
    ],
    "shipping": [
        "Your order has shipped and is out for delivery.",
        "Track your package, estimated delivery is Thursday.",
        "Your parcel was delivered to the front door.",
        "Shipment update: your package is in transit.",
        "Order confirmed, we are packing it and will send tracking soon.",
        "Your handmade order is on its way to you.",
        "Out for delivery today, arriving by end of day.",
        "Here is the tracking number for your recent order.",
    ],
    "travel": [
        "Your flight is confirmed, boarding pass attached.",
        "Reservation confirmed for two nights at the hotel.",
        "Your itinerary: flight, hotel, and dinner reservations.",
        "Check-in is now open for your upcoming trip.",
        "Booking confirmed, your host will send check-in details.",
        "Your hotel reservation in the city is all set.",
        "Departure gate and time for your flight are below.",
        "We look forward to hosting you, check-in is at 3 PM.",
    ],
    "promotions": [
        "Take 40 percent off everything this weekend with code.",
        "An exclusive coupon just for you, discount ends tonight.",
        "Flash sale, deals this good will not last.",
        "Half off your next order, use the code at checkout.",
        "Your favorite items are on sale this week only.",
        "Last chance, your cart is waiting and prices drop tonight.",
        "Save on our house blend, limited time offer.",
        "Buy one get one free on all items in store.",
    ],
    "social": [
        "You have new connection requests waiting for a response.",
        "Someone tagged you in a photo, see it now.",
        "You have new notifications and friend requests.",
        "Someone started following you this week.",
        "You were mentioned in a comment, jump back in.",
        "Your friend just posted an update you might like.",
        "New followers and likes on your recent post.",
        "A new invitation to connect is waiting.",
    ],
    "newsletters": [
        "This week in tech, the five stories you should read.",
        "Your weekly digest of new articles from the blog.",
        "The Monday newsletter with insights, links, and long reads.",
        "This issue: what we learned building in public.",
        "A short note this week about shipping side projects.",
        "This week's tools, reads, and one idea to sit with.",
        "The morning brief on business and markets.",
        "Our latest issue is out, here is what is inside.",
    ],
    "updates": [
        "Security alert: a new sign-in was detected on your account.",
        "We have updated our terms of service, effective next month.",
        "Your subscription will renew automatically on the first.",
        "Scheduled maintenance is planned for this weekend.",
        "A new device signed in to your workspace.",
        "Please verify your account to keep it active.",
        "We updated our privacy policy, review the changes.",
        "Your password was changed successfully.",
    ],
    "support": [
        "Your support ticket has been updated, an agent is on it.",
        "Your case has been resolved, was this helpful?",
        "Sorry you hit a snag, here is how to fix the issue.",
        "A support agent has replied to your question.",
        "We refunded your last charge following up on your case.",
        "Thanks for contacting help desk, we are looking into it.",
        "Your request has been received and assigned to an agent.",
        "Follow up on your reported problem with the app.",
    ],
    "events": [
        "You are invited, RSVP for the launch party on Friday.",
        "Calendar invite for the team offsite next week.",
        "Reminder: the meetup starts in one hour.",
        "You are confirmed for founders night, doors open at seven.",
        "Throwing a small dinner this weekend, hope you can come.",
        "Your ticket for the conference is confirmed.",
        "Please RSVP for the event, space is limited.",
        "Save the date for our upcoming gathering.",
    ],
    "personal": [
        "Are we still on for dinner this weekend?",
        "Can you send me those photos from the trip?",
        "Thanks so much for the birthday wishes, it meant a lot.",
        "Long time no talk, how have you been lately?",
        "We should grab coffee when you are free.",
        "Finally remembered the title of that book I mentioned.",
        "Just checking in to see how you are doing.",
        "Miss you, let's catch up soon over a call.",
    ],
    "spam": [
        "Congratulations, you have won a gift card, claim now.",
        "Urgent, your account will be closed unless you verify immediately.",
        "You have an unclaimed inheritance waiting, reply with your details.",
        "Final notice, claim your free reward now before it is gone.",
        "You are a winner, act now to receive your prize.",
        "Wire transfer needed to release your funds, respond today.",
        "Hot deal, risk free, act now for this one time offer.",
        "Verify your bank details to claim your prize money.",
    ],
}


def seed_examples() -> list[LabeledExample]:
    return [LabeledExample(text=t, label=label) for label, texts in _SEED.items() for t in texts]
