"""Auth interface and default client selection.

Default is a no-op until ``set_client`` is called; tests install
``FakeAuthClient`` via the ``client`` fixture. Production wires the
real ``GoTrueClient`` on first call.
"""
from __future__ import annotations

from app.auth.base import AuthClient, AuthError, Session, User
from app.auth.fake import FakeAuthClient

_client: AuthClient | None = None


def set_client(c: AuthClient) -> None:
    global _client
    _client = c


def client() -> AuthClient:
    global _client
    if _client is None:
        from app.auth.gotrue import GoTrueClient
        from app.config import settings

        s = settings()
        if not s.supabase_anon_key:
            raise RuntimeError(
                "SUPABASE_ANON_KEY must be set for auth. Find it at "
                "Settings → API → anon (public)."
            )
        _client = GoTrueClient(s.supabase_url, s.supabase_anon_key)
    return _client


def reset_for_tests() -> FakeAuthClient:
    fake = FakeAuthClient()
    set_client(fake)
    return fake


__all__ = [
    "AuthClient",
    "AuthError",
    "FakeAuthClient",
    "Session",
    "User",
    "client",
    "reset_for_tests",
    "set_client",
]
