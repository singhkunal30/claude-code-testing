from __future__ import annotations


def _make_entry(client) -> int:
    return client.post("/entries", json={"text": "x", "tags": ["t"]}).json()["id"]


def test_create_highlight(client) -> None:
    eid = _make_entry(client)
    r = client.post("/highlights", json={"entry_id": eid, "note": "key insight"})
    assert r.status_code == 201
    body = r.json()
    assert body["entry_id"] == eid
    assert body["note"] == "key insight"


def test_create_requires_existing_entry(client) -> None:
    r = client.post("/highlights", json={"entry_id": 9999})
    assert r.status_code == 404


def test_multiple_highlights_same_entry(client) -> None:
    eid = _make_entry(client)
    client.post("/highlights", json={"entry_id": eid, "note": "first time"})
    client.post("/highlights", json={"entry_id": eid, "note": "revisited"})

    rows = client.get("/highlights", params={"entry_id": eid}).json()
    assert len(rows) == 2
    notes = {r["note"] for r in rows}
    assert notes == {"first time", "revisited"}


def test_list_and_delete(client) -> None:
    eid = _make_entry(client)
    hid = client.post("/highlights", json={"entry_id": eid}).json()["id"]

    assert any(h["id"] == hid for h in client.get("/highlights").json())
    assert client.delete(f"/highlights/{hid}").status_code == 204
    assert client.get(f"/highlights/{hid}").status_code == 404


def test_highlights_cascade_on_entry_delete(client) -> None:
    eid = _make_entry(client)
    client.post("/highlights", json={"entry_id": eid})
    client.delete(f"/entries/{eid}")
    assert client.get("/highlights", params={"entry_id": eid}).json() == []
