from __future__ import annotations


def _make_entry(client, text: str = "x") -> int:
    return client.post("/entries", json={"text": text, "tags": ["t"]}).json()["id"]


def test_create_and_get(client) -> None:
    r = client.post("/collections", json={"name": "Favorites", "description": "best of"})
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Favorites"
    assert body["entry_ids"] == []

    fetched = client.get(f"/collections/{body['id']}").json()
    assert fetched == body


def test_duplicate_name_conflict(client) -> None:
    client.post("/collections", json={"name": "Favorites"})
    r = client.post("/collections", json={"name": "Favorites"})
    assert r.status_code == 409


def test_add_and_remove_entries(client) -> None:
    cid = client.post("/collections", json={"name": "C"}).json()["id"]
    e1 = _make_entry(client, "a")
    e2 = _make_entry(client, "b")

    r = client.post(f"/collections/{cid}/entries/{e1}")
    assert r.status_code == 201
    client.post(f"/collections/{cid}/entries/{e2}")

    body = client.get(f"/collections/{cid}").json()
    assert sorted(body["entry_ids"]) == sorted([e1, e2])

    # Adding the same entry twice is idempotent.
    client.post(f"/collections/{cid}/entries/{e1}")
    assert len(client.get(f"/collections/{cid}").json()["entry_ids"]) == 2

    assert client.delete(f"/collections/{cid}/entries/{e1}").status_code == 204
    assert client.get(f"/collections/{cid}").json()["entry_ids"] == [e2]


def test_add_entry_validates_existence(client) -> None:
    cid = client.post("/collections", json={"name": "C"}).json()["id"]
    assert client.post(f"/collections/{cid}/entries/9999").status_code == 404
    assert client.post(f"/collections/9999/entries/1").status_code == 404


def test_delete_collection_cascades_links(client) -> None:
    cid = client.post("/collections", json={"name": "C"}).json()["id"]
    eid = _make_entry(client)
    client.post(f"/collections/{cid}/entries/{eid}")

    assert client.delete(f"/collections/{cid}").status_code == 204
    assert client.get(f"/collections/{cid}").status_code == 404


def test_collection_links_cascade_on_entry_delete(client) -> None:
    cid = client.post("/collections", json={"name": "C"}).json()["id"]
    eid = _make_entry(client)
    client.post(f"/collections/{cid}/entries/{eid}")

    client.delete(f"/entries/{eid}")
    assert client.get(f"/collections/{cid}").json()["entry_ids"] == []
