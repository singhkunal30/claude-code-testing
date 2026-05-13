from __future__ import annotations


def _post(client, text: str) -> int:
    return client.post("/entries", json={"text": text, "tags": ["t"]}).json()["id"]


def test_related_ranks_similar_first(client) -> None:
    a = _post(client, "Learned about Python and SQLite WAL mode")
    _post(client, "Took notes on baking sourdough bread today")
    c = _post(client, "Python concurrency with asyncio and sqlite")

    r = client.get(f"/entries/{a}/related", params={"k": 2})
    assert r.status_code == 200
    ids = [e["id"] for e in r.json()]
    assert ids[0] == c  # most similar to A
    assert a not in ids  # excludes self


def test_related_404_for_unknown_entry(client) -> None:
    assert client.get("/entries/9999/related").status_code == 404


def test_related_empty_when_only_self(client) -> None:
    eid = _post(client, "lonely entry")
    assert client.get(f"/entries/{eid}/related").json() == []
