"""Real GoTrue HTTP client.

Talks to <SUPABASE_URL>/auth/v1/ using the anon key. The anon key is what
the GoTrue REST API expects for signup/login; do NOT use service_role here.
"""
from __future__ import annotations

import httpx

from app.auth.base import AuthClient, AuthError, Session, User


class GoTrueClient:
    def __init__(self, base_url: str, anon_key: str) -> None:
        self._http = httpx.Client(
            base_url=f"{base_url}/auth/v1",
            headers={
                "apikey": anon_key,
                "Authorization": f"Bearer {anon_key}",
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )

    def _request(self, method: str, path: str, **kwargs) -> dict:
        r = self._http.request(method, path, **kwargs)
        if r.status_code >= 400:
            detail = r.json().get("msg") or r.json().get("error_description") or r.text
            raise AuthError(r.status_code, detail)
        return r.json() if r.text else {}

    def _session_from(self, body: dict) -> Session:
        user = body.get("user") or {}
        return Session(
            user=User(id=user["id"], email=user["email"]),
            access_token=body["access_token"],
        )

    def signup(self, email: str, password: str) -> Session:
        body = self._request("POST", "/signup", json={"email": email, "password": password})
        # If email confirmation is required, GoTrue returns the user but no
        # session. Tell the caller in that case.
        if "access_token" not in body:
            raise AuthError(202, "Account created; email confirmation required.")
        return self._session_from(body)

    def login(self, email: str, password: str) -> Session:
        body = self._request(
            "POST",
            "/token",
            params={"grant_type": "password"},
            json={"email": email, "password": password},
        )
        return self._session_from(body)

    def verify_token(self, token: str) -> User:
        r = self._http.get("/user", headers={"Authorization": f"Bearer {token}"})
        if r.status_code >= 400:
            raise AuthError(r.status_code, "Invalid or expired token")
        body = r.json()
        return User(id=body["id"], email=body["email"])

    def logout(self, token: str) -> None:
        self._http.post("/logout", headers={"Authorization": f"Bearer {token}"})
