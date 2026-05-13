from __future__ import annotations


def _make_entry(client) -> int:
    return client.post("/entries", json={"text": "x", "tags": ["t"]}).json()["id"]


def test_create_top_level_comment(client) -> None:
    eid = _make_entry(client)
    r = client.post(
        f"/entries/{eid}/comments",
        json={"body": "first!", "author": "alice"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["body"] == "first!"
    assert body["author"] == "alice"
    assert body["parent_comment_id"] is None
    assert body["replies"] == []


def test_threaded_replies(client) -> None:
    eid = _make_entry(client)
    parent = client.post(f"/entries/{eid}/comments", json={"body": "parent"}).json()
    child = client.post(
        f"/entries/{eid}/comments",
        json={"body": "child", "parent_comment_id": parent["id"]},
    ).json()
    grandchild = client.post(
        f"/entries/{eid}/comments",
        json={"body": "grand", "parent_comment_id": child["id"]},
    ).json()

    tree = client.get(f"/entries/{eid}/comments").json()
    assert len(tree) == 1
    assert tree[0]["id"] == parent["id"]
    assert len(tree[0]["replies"]) == 1
    assert tree[0]["replies"][0]["id"] == child["id"]
    assert tree[0]["replies"][0]["replies"][0]["id"] == grandchild["id"]


def test_invalid_parent_rejected(client) -> None:
    eid = _make_entry(client)
    other = _make_entry(client)
    other_comment = client.post(f"/entries/{other}/comments", json={"body": "hi"}).json()

    r = client.post(
        f"/entries/{eid}/comments",
        json={"body": "x", "parent_comment_id": other_comment["id"]},
    )
    assert r.status_code == 400


def test_delete_comment_cascades_replies(client) -> None:
    eid = _make_entry(client)
    parent = client.post(f"/entries/{eid}/comments", json={"body": "parent"}).json()
    client.post(f"/entries/{eid}/comments", json={"body": "child", "parent_comment_id": parent["id"]})

    assert client.delete(f"/comments/{parent['id']}").status_code == 204
    assert client.get(f"/entries/{eid}/comments").json() == []


def test_comments_cascade_on_entry_delete(client) -> None:
    eid = _make_entry(client)
    client.post(f"/entries/{eid}/comments", json={"body": "x"})
    client.delete(f"/entries/{eid}")
    assert client.get(f"/entries/{eid}/comments").status_code == 404
