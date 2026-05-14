"""Cross-tenant isolation tests.

These hit the application-layer scoping (user_id filtering in router code).
Phase 2 will additionally enforce isolation via RLS at the DB layer.
"""
from __future__ import annotations


def test_users_cannot_see_each_others_entries(client, make_user) -> None:
    alice_entry = client.post(
        "/entries", json={"text": "alice secret", "tags": ["t"]}
    ).json()
    bob = make_user("bob@example.com")
    bob_entry = bob.post("/entries", json={"text": "bob secret", "tags": ["t"]}).json()

    alice_list = client.get("/entries").json()
    assert [e["text"] for e in alice_list] == ["alice secret"]

    bob_list = bob.get("/entries").json()
    assert [e["text"] for e in bob_list] == ["bob secret"]

    assert client.get(f"/entries/{bob_entry['id']}").status_code == 404
    assert bob.get(f"/entries/{alice_entry['id']}").status_code == 404


def test_users_cannot_delete_each_others_entries(client, make_user) -> None:
    a = client.post("/entries", json={"text": "x", "tags": ["t"]}).json()
    bob = make_user("bob@example.com")
    assert bob.delete(f"/entries/{a['id']}").status_code == 404
    # Alice's entry is still there.
    assert client.get(f"/entries/{a['id']}").status_code == 200


def test_tags_are_per_user(client, make_user) -> None:
    client.post("/entries", json={"text": "x", "tags": ["python"]})
    bob = make_user("bob@example.com")
    bob.post("/entries", json={"text": "y", "tags": ["python"]})

    assert client.get("/entries/tags/all").json() == {"python": 1}
    assert bob.get("/entries/tags/all").json() == {"python": 1}


def test_collection_name_can_collide_across_users(client, make_user) -> None:
    assert client.post("/collections", json={"name": "Favourites"}).status_code == 201
    bob = make_user("bob@example.com")
    assert bob.post("/collections", json={"name": "Favourites"}).status_code == 201


def test_cannot_react_on_other_users_entry(client, make_user) -> None:
    a = client.post("/entries", json={"text": "x", "tags": ["t"]}).json()
    bob = make_user("bob@example.com")
    assert bob.post(f"/entries/{a['id']}/reactions", json={"emoji": "🔥"}).status_code == 404


def test_cannot_share_other_users_entry(client, make_user) -> None:
    a = client.post("/entries", json={"text": "x", "tags": ["t"]}).json()
    bob = make_user("bob@example.com")
    assert bob.post(f"/entries/{a['id']}/share").status_code == 404


def test_share_view_is_public_for_token_holder(client, make_user) -> None:
    a = client.post("/entries", json={"text": "shareable", "tags": ["t"]}).json()
    info = client.post(f"/entries/{a['id']}/share").json()
    from fastapi.testclient import TestClient
    from app.main import app

    anon = TestClient(app)
    r = anon.get(info["url"])
    assert r.status_code == 200
    assert "shareable" in r.text


def test_export_is_per_user(client, make_user) -> None:
    client.post("/entries", json={"text": "alice", "tags": ["t"]})
    bob = make_user("bob@example.com")
    bob.post("/entries", json={"text": "bob", "tags": ["t"]})

    alice_export = client.get("/export.json").json()
    bob_export = bob.get("/export.json").json()
    assert [e["text"] for e in alice_export] == ["alice"]
    assert [e["text"] for e in bob_export] == ["bob"]


def test_stats_isolated_per_user(client, make_user) -> None:
    client.post("/entries", json={"text": "a", "tags": ["t"]})
    bob = make_user("bob@example.com")
    bob.post("/entries", json={"text": "b1", "tags": ["t"]})
    bob.post("/entries", json={"text": "b2", "tags": ["t"]})

    assert client.get("/stats").json()["total_entries"] == 1
    assert bob.get("/stats").json()["total_entries"] == 2
