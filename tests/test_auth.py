from __future__ import annotations


def test_signup_returns_user_and_sets_cookie(anon_client) -> None:
    r = anon_client.post(
        "/auth/signup",
        json={"email": "new@example.com", "password": "hunter22"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "new@example.com"
    assert body["user_id"]
    assert "til_session" in anon_client.cookies


def test_signup_duplicate_email_409(anon_client) -> None:
    anon_client.post("/auth/signup", json={"email": "dup@example.com", "password": "hunter22"})
    r = anon_client.post(
        "/auth/signup", json={"email": "dup@example.com", "password": "hunter22"}
    )
    assert r.status_code == 409


def test_signup_short_password_422(anon_client) -> None:
    r = anon_client.post(
        "/auth/signup", json={"email": "x@y.com", "password": "short"}
    )
    assert r.status_code == 422


def test_login_then_me(anon_client) -> None:
    anon_client.post("/auth/signup", json={"email": "lo@example.com", "password": "hunter22"})
    anon_client.post("/auth/logout")
    assert anon_client.get("/auth/me").status_code == 401

    r = anon_client.post(
        "/auth/login", json={"email": "lo@example.com", "password": "hunter22"}
    )
    assert r.status_code == 200
    me = anon_client.get("/auth/me").json()
    assert me["email"] == "lo@example.com"


def test_login_wrong_password_401(anon_client) -> None:
    anon_client.post("/auth/signup", json={"email": "x@example.com", "password": "hunter22"})
    anon_client.post("/auth/logout")
    r = anon_client.post(
        "/auth/login", json={"email": "x@example.com", "password": "nope42"}
    )
    assert r.status_code == 401


def test_protected_endpoint_requires_auth(anon_client) -> None:
    assert anon_client.get("/entries").status_code == 401
    assert anon_client.post("/entries", json={"text": "x"}).status_code == 401


def test_logout_clears_cookie(client) -> None:
    assert client.get("/auth/me").status_code == 200
    client.post("/auth/logout")
    assert client.get("/auth/me").status_code == 401


def test_ui_redirects_anon_to_login(anon_client) -> None:
    r = anon_client.get("/", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_login_page_renders(anon_client) -> None:
    r = anon_client.get("/login")
    assert r.status_code == 200
    assert "Sign in" in r.text


def test_signup_via_ui_form_creates_session(anon_client) -> None:
    r = anon_client.post(
        "/signup",
        data={"email": "uiuser@example.com", "password": "hunter22"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/"
    assert "til_session" in anon_client.cookies
