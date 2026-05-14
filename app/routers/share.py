from __future__ import annotations

import secrets

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.supabase import client

router = APIRouter(tags=["share"])


class ShareInfo(BaseModel):
    entry_id: int
    token: str
    url: str


def _share_url(token: str) -> str:
    return f"/share/{token}"


def _load_entry(entry_id: int) -> dict:
    rows = client().select("entries", filters={"id": ("eq", entry_id)})
    if not rows:
        raise HTTPException(status_code=404, detail="Entry not found")
    return rows[0]


@router.post("/entries/{entry_id}/share", response_model=ShareInfo, status_code=201)
def enable_share(entry_id: int) -> ShareInfo:
    sb = client()
    row = _load_entry(entry_id)
    token = row.get("share_token") or secrets.token_urlsafe(16)
    if not row.get("share_token"):
        sb.update("entries", {"share_token": token}, filters={"id": ("eq", entry_id)})
    return ShareInfo(entry_id=entry_id, token=token, url=_share_url(token))


@router.get("/entries/{entry_id}/share", response_model=ShareInfo)
def get_share(entry_id: int) -> ShareInfo:
    row = _load_entry(entry_id)
    token = row.get("share_token")
    if not token:
        raise HTTPException(status_code=404, detail="Entry is not shared")
    return ShareInfo(entry_id=entry_id, token=token, url=_share_url(token))


@router.delete("/entries/{entry_id}/share", status_code=204)
def disable_share(entry_id: int) -> None:
    sb = client()
    row = _load_entry(entry_id)
    if not row.get("share_token"):
        raise HTTPException(status_code=404, detail="Entry is not shared")
    sb.update("entries", {"share_token": None}, filters={"id": ("eq", entry_id)})
