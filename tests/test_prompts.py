from __future__ import annotations


def test_create_and_list(client) -> None:
    r = client.post("/prompts", json={"text": "What surprised you today?"})
    assert r.status_code == 201
    body = r.json()
    assert body["text"] == "What surprised you today?"
    assert body["active"] is True

    rows = client.get("/prompts").json()
    assert len(rows) == 1


def test_filter_by_active(client) -> None:
    client.post("/prompts", json={"text": "live", "active": True})
    client.post("/prompts", json={"text": "dead", "active": False})

    active = client.get("/prompts", params={"active": "true"}).json()
    inactive = client.get("/prompts", params={"active": "false"}).json()
    assert [p["text"] for p in active] == ["live"]
    assert [p["text"] for p in inactive] == ["dead"]


def test_random_returns_active_only(client) -> None:
    client.post("/prompts", json={"text": "only", "active": True})
    client.post("/prompts", json={"text": "hidden", "active": False})

    for _ in range(10):
        body = client.get("/prompts/random").json()
        assert body["text"] == "only"


def test_random_404_when_none_active(client) -> None:
    client.post("/prompts", json={"text": "hidden", "active": False})
    assert client.get("/prompts/random").status_code == 404


def test_delete(client) -> None:
    pid = client.post("/prompts", json={"text": "x"}).json()["id"]
    assert client.delete(f"/prompts/{pid}").status_code == 204
    assert client.get(f"/prompts/{pid}").status_code == 404
