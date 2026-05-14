from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient

from app.auth import reset_for_tests as reset_auth_for_tests
from app.supabase import reset_for_tests


@pytest.fixture()
def anon_client() -> Iterator[TestClient]:
    """Fresh app + empty in-memory Supabase + empty in-memory auth, no session."""
    reset_for_tests()
    reset_auth_for_tests()
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def client(anon_client: TestClient) -> TestClient:
    """A TestClient already logged in as 'alice@example.com'.

    Almost every test wants this — auth gates every protected route, so an
    anonymous client gets 401s/redirects on basically everything.
    """
    r = anon_client.post(
        "/auth/signup",
        json={"email": "alice@example.com", "password": "hunter22"},
    )
    assert r.status_code == 201, r.text
    return anon_client


@pytest.fixture()
def make_user(client: TestClient) -> Callable[[str], TestClient]:
    """Factory for additional logged-in TestClients on the same in-memory app.

    Use for cross-tenant tests: ``bob = make_user("bob@example.com")``.
    All clients share the same Supabase fake; only the cookie/identity differs.
    """
    from app.main import app

    def _make(email: str, password: str = "hunter22") -> TestClient:
        c = TestClient(app)
        r = c.post("/auth/signup", json={"email": email, "password": password})
        assert r.status_code == 201, r.text
        return c

    return _make
