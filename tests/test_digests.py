from __future__ import annotations

from datetime import date, timedelta


def test_generate_week_digest_includes_recent_entries(client) -> None:
    client.post("/entries", json={"text": "alpha learning", "tags": ["a"]})
    client.post("/entries", json={"text": "beta learning", "tags": ["b"]})

    today = date.today()
    r = client.post("/digests/generate", json={"period": "week", "end_date": today.isoformat()})
    assert r.status_code == 201
    body = r.json()
    assert body["period"] == "week"
    assert body["start_date"] == (today - timedelta(days=6)).isoformat()
    assert body["end_date"] == today.isoformat()
    assert "alpha learning" in body["content"]
    assert "beta learning" in body["content"]
    assert len(body["entry_ids"]) == 2


def test_get_digest_roundtrip(client) -> None:
    created = client.post("/digests/generate", json={"period": "week"}).json()
    r = client.get(f"/digests/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_unsupported_period_returns_400(client) -> None:
    r = client.post("/digests/generate", json={"period": "year"})
    # Pydantic Literal validation kicks in before our handler.
    assert r.status_code == 422
