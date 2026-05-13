from __future__ import annotations


def test_home_renders_html(client) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "TIL Journal" in r.text
    assert "<form" in r.text


def test_create_entry_via_form_then_appears_on_home(client) -> None:
    r = client.post(
        "/ui/entries",
        data={"text": "form-submitted entry", "tags": "alpha, beta"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/"

    r = client.get("/")
    assert "form-submitted entry" in r.text
    assert "alpha" in r.text and "beta" in r.text


def test_create_bookmark_via_form(client) -> None:
    r = client.post(
        "/ui/bookmarks",
        data={"url": "https://example.com", "title": "Example"},
        follow_redirects=False,
    )
    assert r.status_code == 303

    r = client.get("/")
    assert "https://example.com" in r.text
    assert "Example" in r.text


def test_digests_page_generates_and_lists(client) -> None:
    r = client.post(
        "/ui/digests/generate", data={"period": "week"}, follow_redirects=False
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/ui/digests"

    r = client.get("/ui/digests")
    assert r.status_code == 200
    assert "Digests" in r.text
