"""Session cookie handling + FastAPI dependencies.

We stash the GoTrue access_token in an HttpOnly cookie. Each request:

1. Read the cookie.
2. Ask the auth client to verify it.
3. Resolve to a `User` and pass it into the route via `Depends(current_user)`.

Anonymous routes use `Depends(optional_user)` which returns `None`.
"""
from __future__ import annotations

from fastapi import Cookie, HTTPException, Response

from app.auth import client as auth_client
from app.auth.base import AuthError, Session, User

COOKIE_NAME = "til_session"


def set_session_cookie(response: Response, session: Session) -> None:
    response.set_cookie(
        COOKIE_NAME,
        session.access_token,
        httponly=True,
        samesite="lax",
        secure=False,  # set True behind HTTPS in production
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


def optional_user(til_session: str | None = Cookie(default=None)) -> User | None:
    if not til_session:
        return None
    try:
        return auth_client().verify_token(til_session)
    except AuthError:
        return None


def current_user(til_session: str | None = Cookie(default=None)) -> User:
    if not til_session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return auth_client().verify_token(til_session)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=e.message)


class RedirectToLogin(Exception):
    """Raised by UI dependencies when the visitor is anonymous."""


def ui_user(til_session: str | None = Cookie(default=None)) -> User:
    """Same as current_user but raises RedirectToLogin instead of 401.

    Wired to a global exception handler in app.main that turns the exception
    into a 303 redirect to /login.
    """
    if not til_session:
        raise RedirectToLogin()
    try:
        return auth_client().verify_token(til_session)
    except AuthError:
        raise RedirectToLogin()
