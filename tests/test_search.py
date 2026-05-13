from __future__ import annotations


def test_search_matches_text_case_insensitive(client) -> None:
    client.post("/entries", json={"text": "Learned about SQLite WAL mode", "tags": ["t"]})
    client.post("/entries", json={"text": "Took notes on Postgres VACUUM", "tags": ["t"]})

    r = client.get("/entries/search", params={"q": "sqlite"})
    assert r.status_code == 200
    bodies = r.json()
    assert len(bodies) == 1
    assert "SQLite" in bodies[0]["text"]


def test_search_matches_source(client) -> None:
    client.post("/entries", json={"text": "x", "tags": ["t"], "source": "https://supabase.com/docs"})
    client.post("/entries", json={"text": "y", "tags": ["t"], "source": "https://other.com"})

    r = client.get("/entries/search", params={"q": "supabase"})
    bodies = r.json()
    assert len(bodies) == 1
    assert bodies[0]["source"].startswith("https://supabase.com")


def test_search_returns_empty_when_no_match(client) -> None:
    client.post("/entries", json={"text": "nothing relevant", "tags": ["t"]})
    assert client.get("/entries/search", params={"q": "zzz"}).json() == []


def test_search_validates_query(client) -> None:
    assert client.get("/entries/search").status_code == 422
