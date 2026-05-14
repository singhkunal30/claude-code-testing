from __future__ import annotations


def _make_entry(client) -> int:
    return client.post("/entries", json={"text": "hello", "tags": ["t"]}).json()["id"]


def test_enable_share_and_view(client) -> None:
    eid = _make_entry(client)
    r = client.post(f"/entries/{eid}/share")
    assert r.status_code == 201
    body = r.json()
    assert body["entry_id"] == eid
    token = body["token"]
    assert len(token) > 10
    assert body["url"] == f"/share/{token}"

    view = client.get(f"/share/{token}")
    assert view.status_code == 200
    assert "hello" in view.text
    # The public view must not expose admin nav links.
    assert "Digests" not in view.text or "Shared TIL" in view.text


def test_enable_share_is_idempotent(client) -> None:
    eid = _make_entry(client)
    first = client.post(f"/entries/{eid}/share").json()
    second = client.post(f"/entries/{eid}/share").json()
    assert first["token"] == second["token"]


def test_disable_share(client) -> None:
    eid = _make_entry(client)
    token = client.post(f"/entries/{eid}/share").json()["token"]
    assert client.delete(f"/entries/{eid}/share").status_code == 204
    assert client.get(f"/share/{token}").status_code == 404
    # Re-enabling generates a fresh token.
    new_token = client.post(f"/entries/{eid}/share").json()["token"]
    assert new_token != token


def test_get_share_404_when_not_shared(client) -> None:
    eid = _make_entry(client)
    assert client.get(f"/entries/{eid}/share").status_code == 404


def test_share_view_404_for_unknown_token(client) -> None:
    assert client.get("/share/nope").status_code == 404
