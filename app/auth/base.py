from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class User(BaseModel):
    id: str  # UUID
    email: str


class Session(BaseModel):
    user: User
    access_token: str


class AuthError(Exception):
    """Raised when GoTrue rejects a credential or token."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class AuthClient(Protocol):
    def signup(self, email: str, password: str) -> Session: ...
    def login(self, email: str, password: str) -> Session: ...
    def verify_token(self, token: str) -> User: ...
    def logout(self, token: str) -> None: ...
