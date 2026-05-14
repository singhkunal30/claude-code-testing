from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from app.auth import client as auth_client
from app.auth.base import AuthError, User
from app.auth.session import (
    COOKIE_NAME,
    clear_session_cookie,
    current_user,
    set_session_cookie,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=6, max_length=128)


class AuthResponse(BaseModel):
    user_id: str
    email: str


@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(payload: Credentials, response: Response) -> AuthResponse:
    try:
        session = auth_client().signup(payload.email, payload.password)
    except AuthError as e:
        raise HTTPException(status_code=e.status, detail=e.message)
    set_session_cookie(response, session)
    return AuthResponse(user_id=session.user.id, email=session.user.email)


@router.post("/login", response_model=AuthResponse)
def login(payload: Credentials, response: Response) -> AuthResponse:
    try:
        session = auth_client().login(payload.email, payload.password)
    except AuthError as e:
        raise HTTPException(status_code=e.status, detail=e.message)
    set_session_cookie(response, session)
    return AuthResponse(user_id=session.user.id, email=session.user.email)


@router.post("/logout", status_code=204)
def logout(response: Response, til_session: str | None = Cookie(default=None)) -> None:
    if til_session:
        try:
            auth_client().logout(til_session)
        except AuthError:
            pass
    clear_session_cookie(response)


@router.get("/me", response_model=AuthResponse)
def me(user: User = Depends(current_user)) -> AuthResponse:
    return AuthResponse(user_id=user.id, email=user.email)


__all__ = ["router", "COOKIE_NAME"]
