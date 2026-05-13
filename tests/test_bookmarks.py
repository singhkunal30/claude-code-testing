from __future__ import annotations


def test_create_and_get(client) -> None:
    r = client.post(
        "/bookmarks",
        json={
            "url": "https://example.com",
            "title": "Example",
            "tags": ["reference", "docs"],
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["url"] == "https://example.com"
    assert body["title"] == "Example"
    assert body["tags"] == ["docs", "reference"]  # sorted by name

    r = client.get(f"/bookmarks/{body['id']}")
    assert r.status_code == 200
    assert r.json() == body


def test_list_filter_by_tag(client) -> None:
    client.post("/bookmarks", json={"url": "https://a.example", "tags": ["a"]})
    client.post("/bookmarks", json={"url": "https://b.example", "tags": ["b"]})

    r = client.get("/bookmarks", params={"tag": "a"})
    assert r.status_code == 200
    bodies = r.json()
    assert len(bodies) == 1
    assert bodies[0]["url"] == "https://a.example"


def test_get_404(client) -> None:
    assert client.get("/bookmarks/9999").status_code == 404


def test_delete_cascades_tags(client) -> None:
    created = client.post(
        "/bookmarks", json={"url": "https://example.com", "tags": ["alpha"]}
    ).json()
    assert client.delete(f"/bookmarks/{created['id']}").status_code == 204
    assert client.get(f"/bookmarks/{created['id']}").status_code == 404
    # Bookmark deletion should not affect Entry tag counts
    assert client.get("/entries/tags/all").json() == {}
