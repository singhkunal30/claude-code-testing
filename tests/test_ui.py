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


def test_home_renders_markdown(client) -> None:
    client.post("/entries", json={"text": "**important**", "tags": ["t"]})
    text = client.get("/").text
    assert "<strong>important</strong>" in text


def test_home_search_filters(client) -> None:
    client.post("/entries", json={"text": "Postgres tips", "tags": ["t"]})
    client.post("/entries", json={"text": "Sourdough", "tags": ["t"]})
    text = client.get("/", params={"q": "postgres"}).text
    assert "Postgres" in text
    assert "Sourdough" not in text


def test_home_shows_daily_prompt_banner(client) -> None:
    client.post("/prompts", json={"text": "What stood out today?"})
    text = client.get("/").text
    assert "Today's prompt" in text
    assert "What stood out today?" in text


def test_react_via_form_updates_counts(client) -> None:
    eid = client.post("/entries", json={"text": "x", "tags": ["t"]}).json()["id"]
    r = client.post(
        f"/ui/entries/{eid}/react", data={"emoji": "🔥"}, follow_redirects=False
    )
    assert r.status_code == 303
    home = client.get("/").text
    assert "🔥 1" in home


def test_highlight_toggle(client) -> None:
    eid = client.post("/entries", json={"text": "x", "tags": ["t"]}).json()["id"]
    client.post(f"/ui/entries/{eid}/highlight", follow_redirects=False)
    assert "★ highlighted" in client.get("/").text
    client.post(f"/ui/entries/{eid}/highlight", follow_redirects=False)
    assert "★ highlighted" not in client.get("/").text


def test_share_toggle_and_public_view(client) -> None:
    eid = client.post("/entries", json={"text": "public **knowledge**", "tags": ["t"]}).json()["id"]
    client.post(f"/ui/entries/{eid}/share/toggle", follow_redirects=False)
    home = client.get("/").text
    assert "🔗 shared" in home

    # Pull the share URL via API for verification.
    info = client.get(f"/entries/{eid}/share").json()
    view = client.get(info["url"])
    assert view.status_code == 200
    assert "<strong>knowledge</strong>" in view.text


def test_stats_page(client) -> None:
    client.post("/entries", json={"text": "x", "tags": ["python"]})
    text = client.get("/ui/stats").text
    assert "Total entries" in text
    assert "python" in text


def test_ask_page_get_and_post(client) -> None:
    client.post("/entries", json={"text": "Python decorators", "tags": ["t"]})
    assert client.get("/ui/ask").status_code == 200
    r = client.post(
        "/ui/ask", data={"question": "tell me about python"}, follow_redirects=False
    )
    assert r.status_code == 200
    assert "Answer" in r.text
    assert "Cited sources" in r.text
