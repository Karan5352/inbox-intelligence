"""API integration tests against a seeded synthetic inbox."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True


def test_list_and_filter_emails(seeded_client: TestClient):
    page = seeded_client.get("/emails?limit=5").json()
    assert page["total"] > 0
    assert len(page["items"]) == 5
    assert {"category", "confidence", "reason", "category_source"} <= page["items"][0].keys()

    shipping = seeded_client.get("/emails?category=shipping").json()
    assert all(e["category"] == "shipping" for e in shipping["items"])


def test_search(seeded_client: TestClient):
    res = seeded_client.get("/emails?search=invoice").json()
    assert res["total"] >= 1


def test_categories_have_counts(seeded_client: TestClient):
    cats = seeded_client.get("/categories").json()
    assert any(c["count"] > 0 for c in cats)
    assert all({"slug", "name", "color", "icon"} <= c.keys() for c in cats)


def test_insights_shape(seeded_client: TestClient):
    ins = seeded_client.get("/insights").json()
    assert ins["total_emails"] > 0
    assert ins["by_category"]
    assert ins["rule_vs_ml"]
    assert ins["volume_by_day"]


def test_bulk_action_dry_run_then_apply(seeded_client: TestClient):
    dry = seeded_client.post(
        "/actions/bulk", json={"action": "archive", "category": "spam", "dry_run": True}
    ).json()
    assert dry["dry_run"] is True and dry["affected"] >= 0

    wet = seeded_client.post(
        "/actions/bulk", json={"action": "archive", "category": "spam", "dry_run": False}
    ).json()
    assert wet["dry_run"] is False
    # Archived spam should no longer appear in the default (non-archived) listing.
    remaining = seeded_client.get("/emails?category=spam").json()
    assert remaining["total"] == 0


def test_invalid_recategorize_is_rejected(seeded_client: TestClient):
    res = seeded_client.post(
        "/actions/bulk",
        json={
            "action": "recategorize",
            "email_ids": [1],
            "value": "not_a_category",
            "dry_run": False,
        },
    )
    assert res.status_code == 422
