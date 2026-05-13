from __future__ import annotations


def test_stats_empty(client) -> None:
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["total_entries"] == 0
    assert body["current_streak_days"] == 0
    assert body["longest_streak_days"] == 0
    assert body["top_tags"] == {}
    assert len(body["weekly_counts"]) == 12


def test_stats_counts_and_streak(client) -> None:
    client.post("/entries", json={"text": "one", "tags": ["python"]})
    client.post("/entries", json={"text": "two", "tags": ["python", "fastapi"]})

    body = client.get("/stats").json()
    assert body["total_entries"] == 2
    assert body["entries_this_week"] == 2
    # Both rows are dated 'today' in the fake, so current streak is 1 day.
    assert body["current_streak_days"] == 1
    assert body["longest_streak_days"] == 1
    assert body["top_tags"] == {"python": 2, "fastapi": 1}


def test_stats_weekly_counts_track_this_week(client) -> None:
    client.post("/entries", json={"text": "x", "tags": ["t"]})
    body = client.get("/stats").json()
    # The current week bucket should have 1 entry.
    assert body["weekly_counts"][-1]["count"] == 1
