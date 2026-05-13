from __future__ import annotations


def test_create_with_auto_tags(client) -> None:
    r = client.post("/entries", json={"text": "Learned about SQLite WAL mode and journals"})
    assert r.status_code == 201
    body = r.json()
    assert body["text"].startswith("Learned about SQLite")
    assert body["tags"], "expected auto-tags from FakeLLMClient"
    assert "sqlite" in body["tags"]


def test_create_with_explicit_tags_skips_llm(client) -> None:
    r = client.post(
        "/entries",
        json={"text": "anything", "tags": ["one", "two"]},
    )
    assert r.status_code == 201
    assert r.json()["tags"] == ["one", "two"]


def test_list_filter_by_tag(client) -> None:
    client.post("/entries", json={"text": "alpha", "tags": ["a"]})
    client.post("/entries", json={"text": "beta", "tags": ["b"]})

    r = client.get("/entries", params={"tag": "a"})
    assert r.status_code == 200
    bodies = r.json()
    assert len(bodies) == 1
    assert bodies[0]["text"] == "alpha"


def test_get_404(client) -> None:
    assert client.get("/entries/9999").status_code == 404


def test_delete(client) -> None:
    created = client.post("/entries", json={"text": "x", "tags": ["t"]}).json()
    assert client.delete(f"/entries/{created['id']}").status_code == 204
    assert client.get(f"/entries/{created['id']}").status_code == 404


def test_tags_counts(client) -> None:
    client.post("/entries", json={"text": "x", "tags": ["python", "fastapi"]})
    client.post("/entries", json={"text": "y", "tags": ["python"]})

    r = client.get("/entries/tags/all")
    assert r.status_code == 200
    assert r.json() == {"python": 2, "fastapi": 1}
