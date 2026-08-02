"""Tests for the correction learning loop and automations."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.automation import rules as automation_rules


def test_correction_relabels_and_protects_email(seeded_client: TestClient):
    first = seeded_client.get("/emails?limit=1").json()["items"][0]
    eid = first["id"]

    res = seeded_client.post("/corrections", json={"email_id": eid, "to_category": "personal"})
    assert res.status_code == 201

    after = seeded_client.get(f"/emails/{eid}").json()
    assert after["category"] == "personal"
    assert after["category_source"] == "correction"
    assert after["confidence"] == 1.0


def test_correction_updates_learning_status(seeded_client: TestClient):
    before = seeded_client.get("/learning/status").json()["corrections"]
    eid = seeded_client.get("/emails?limit=1").json()["items"][0]["id"]
    seeded_client.post("/corrections", json={"email_id": eid, "to_category": "work"})
    after = seeded_client.get("/learning/status").json()
    assert after["corrections"] == before + 1
    assert after["classifier_examples"] > 40  # prototypes remain seeded


def test_correction_invalid_category_rejected(seeded_client: TestClient):
    eid = seeded_client.get("/emails?limit=1").json()["items"][0]["id"]
    res = seeded_client.post("/corrections", json={"email_id": eid, "to_category": "bogus"})
    assert res.status_code == 422


def test_correction_missing_email_404(seeded_client: TestClient):
    res = seeded_client.post("/corrections", json={"email_id": 999999, "to_category": "work"})
    assert res.status_code == 404


def test_automation_matcher():
    email = {"category": "promotions", "sender": "deals@x.com", "subject": "Sale", "is_read": False}
    assert automation_rules.matches(
        {"field": "category", "op": "equals", "value": "promotions"}, email
    )
    assert automation_rules.matches({"field": "subject", "op": "contains", "value": "sale"}, email)
    assert automation_rules.matches({"field": "unread", "op": "is_true", "value": ""}, email)
    assert not automation_rules.matches(
        {"field": "category", "op": "equals", "value": "work"}, email
    )


def test_automation_create_and_run(seeded_client: TestClient):
    created = seeded_client.post(
        "/automations",
        json={
            "name": "Archive promotions",
            "condition": {"field": "category", "op": "equals", "value": "promotions"},
            "action": {"type": "archive"},
        },
    )
    assert created.status_code == 201

    dry = seeded_client.post("/automations/run?dry_run=true").json()
    assert dry["matched"] >= 0 and dry["applied"] == 0

    wet = seeded_client.post("/automations/run?dry_run=false").json()
    assert wet["applied"] == wet["matched"]
