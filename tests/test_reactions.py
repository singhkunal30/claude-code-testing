from __future__ import annotations


def _make_entry(client) -> int:
    return client.post("/entries", json={"text": "x", "tags": ["t"]}).json()["id"]


def test_react_increments_count(client) -> None:
    eid = _make_entry(client)
    r1 = client.post(f"/entries/{eid}/reactions", json={"emoji": "fire"})
    assert r1.status_code == 201
    assert r1.json() == {"entry_id": eid, "emoji": "fire", "count": 1}

    r2 = client.post(f"/entries/{eid}/reactions", json={"emoji": "fire"})
    assert r2.json()["count"] == 2


def test_react_supports_multiple_emojis(client) -> None:
    eid = _make_entry(client)
    client.post(f"/entries/{eid}/reactions", json={"emoji": "fire"})
    client.post(f"/entries/{eid}/reactions", json={"emoji": "fire"})
    client.post(f"/entries/{eid}/reactions", json={"emoji": "mindblown"})

    rows = client.get(f"/entries/{eid}/reactions").json()
    counts = {r["emoji"]: r["count"] for r in rows}
    assert counts == {"fire": 2, "mindblown": 1}


def test_react_404_unknown_entry(client) -> None:
    assert client.post("/entries/9999/reactions", json={"emoji": "x"}).status_code == 404


def test_delete_reaction(client) -> None:
    eid = _make_entry(client)
    client.post(f"/entries/{eid}/reactions", json={"emoji": "fire"})
    assert client.delete(f"/entries/{eid}/reactions/fire").status_code == 204
    assert client.get(f"/entries/{eid}/reactions").json() == []


def test_reactions_cascade_on_entry_delete(client) -> None:
    eid = _make_entry(client)
    client.post(f"/entries/{eid}/reactions", json={"emoji": "fire"})
    assert client.delete(f"/entries/{eid}").status_code == 204
    assert client.get(f"/entries/{eid}/reactions").status_code == 404
