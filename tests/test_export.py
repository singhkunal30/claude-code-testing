from __future__ import annotations


def test_export_json(client) -> None:
    client.post("/entries", json={"text": "first", "tags": ["a"]})
    client.post("/entries", json={"text": "second", "tags": ["b"]})

    r = client.get("/export.json")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    texts = {e["text"] for e in body}
    assert texts == {"first", "second"}
    # share_token must not leak into the export.
    assert "share_token" not in body[0]


def test_export_markdown(client) -> None:
    client.post("/entries", json={"text": "alpha", "tags": ["a"], "source": "https://x"})
    client.post("/entries", json={"text": "beta", "tags": ["b"]})

    r = client.get("/export.md")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/markdown")
    assert "attachment" in r.headers.get("content-disposition", "")
    md = r.text
    assert "# TIL Journal" in md
    assert "alpha" in md
    assert "beta" in md
    assert "[source](https://x)" in md


def test_export_empty(client) -> None:
    assert client.get("/export.json").json() == []
    assert "# TIL Journal" in client.get("/export.md").text
