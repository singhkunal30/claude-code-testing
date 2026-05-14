"""In-memory auth client that mimics GoTrue for tests + offline dev.

Stores users in a dict; issues opaque tokens (not real JWTs). Deliberately
does not implement features beyond signup/login/verify/logout — those land
in the real GoTrue client.
"""
from __future__ import annotations

import hashlib
import secrets
import uuid

from app.auth.base import AuthClient, AuthError, Session, User


def _hash(password: str, salt: bytes) -> bytes:
    # Cheap salted SHA-256 — this is the test fake, not production auth.
    # Real password hashing lives in GoTrue.
    return hashlib.sha256(salt + password.encode("utf-8")).digest()


class FakeAuthClient:
    def __init__(self) -> None:
        # email -> {id, password_hash, salt}
        self._users: dict[str, dict] = {}
        # token -> user_id
        self._tokens: dict[str, str] = {}
        # user_id -> email (for verify)
        self._by_id: dict[str, str] = {}

    def signup(self, email: str, password: str) -> Session:
        email = email.strip().lower()
        if not email or "@" not in email:
            raise AuthError(422, "Invalid email")
        if len(password) < 6:
            raise AuthError(422, "Password must be at least 6 characters")
        if email in self._users:
            raise AuthError(409, "User already registered")
        salt = secrets.token_bytes(16)
        user_id = str(uuid.uuid4())
        self._users[email] = {"id": user_id, "salt": salt, "hash": _hash(password, salt)}
        self._by_id[user_id] = email
        token = secrets.token_urlsafe(32)
        self._tokens[token] = user_id
        return Session(user=User(id=user_id, email=email), access_token=token)

    def login(self, email: str, password: str) -> Session:
        email = email.strip().lower()
        record = self._users.get(email)
        if not record or _hash(password, record["salt"]) != record["hash"]:
            raise AuthError(401, "Invalid email or password")
        token = secrets.token_urlsafe(32)
        self._tokens[token] = record["id"]
        return Session(user=User(id=record["id"], email=email), access_token=token)

    def verify_token(self, token: str) -> User:
        user_id = self._tokens.get(token)
        if not user_id:
            raise AuthError(401, "Invalid or expired token")
        return User(id=user_id, email=self._by_id[user_id])

    def logout(self, token: str) -> None:
        self._tokens.pop(token, None)


# A protocol-conformance assertion at import time. Pure documentation; mypy
# would catch this, but we don't run mypy yet.
_: AuthClient = FakeAuthClient()
