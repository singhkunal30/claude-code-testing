from __future__ import annotations


def _post(client, text: str) -> int:
    return client.post("/entries", json={"text": text, "tags": ["t"]}).json()["id"]


def test_ask_returns_relevant_sources(client) -> None:
    py = _post(client, "Python decorators and metaclasses")
    _post(client, "Sourdough hydration ratios")
    _post(client, "How to nap during the day")

    r = client.post("/ask", json={"question": "tell me about python", "k": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["question"] == "tell me about python"
    source_ids = [s["id"] for s in body["sources"]]
    assert py in source_ids
    assert body["answer"]


def test_ask_no_sources_when_db_empty(client) -> None:
    r = client.post("/ask", json={"question": "anything?"}).json()
    assert r["sources"] == []
    assert "don't have" in r["answer"].lower() or "no" in r["answer"].lower()


def test_ask_validates_question(client) -> None:
    assert client.post("/ask", json={"question": ""}).status_code == 422
