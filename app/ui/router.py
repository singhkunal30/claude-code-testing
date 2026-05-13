"""HTML UI for the TIL journal. Form-driven, no JS framework.

Parses application/x-www-form-urlencoded bodies via stdlib urllib.parse
(no python-multipart dependency).
"""
from __future__ import annotations

import urllib.parse

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.models.bookmark import BookmarkCreate
from app.models.digest import DigestCreate
from app.models.entry import EntryCreate
from app.routers import bookmarks as bookmarks_router
from app.routers import digests as digests_router
from app.routers import entries as entries_router
from app.ui import templates

router = APIRouter(tags=["ui"], include_in_schema=False)


async def _form(request: Request) -> dict[str, str]:
    body = await request.body()
    if not body:
        return {}
    parsed = urllib.parse.parse_qs(body.decode("utf-8"), keep_blank_values=False)
    return {k: v[0] for k, v in parsed.items()}


def _split_tags(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    tags = [t.strip() for t in raw.split(",") if t.strip()]
    return tags or None


@router.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    entries = entries_router.list_entries(tag=None, since=None, limit=20)
    bookmarks = bookmarks_router.list_bookmarks(tag=None, limit=20)
    return HTMLResponse(templates.home(entries, bookmarks))


@router.post("/ui/entries")
async def create_entry(request: Request) -> RedirectResponse:
    form = await _form(request)
    text = form.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text required")
    entries_router.create_entry(
        EntryCreate(
            text=text,
            source=form.get("source") or None,
            tags=_split_tags(form.get("tags")),
        )
    )
    return RedirectResponse(url="/", status_code=303)


@router.post("/ui/entries/{entry_id}/delete")
def delete_entry(entry_id: int) -> RedirectResponse:
    entries_router.delete_entry(entry_id)
    return RedirectResponse(url="/", status_code=303)


@router.post("/ui/bookmarks")
async def create_bookmark(request: Request) -> RedirectResponse:
    form = await _form(request)
    url = form.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url required")
    bookmarks_router.create_bookmark(
        BookmarkCreate(
            url=url,
            title=form.get("title") or None,
            notes=form.get("notes") or None,
            tags=_split_tags(form.get("tags")),
        )
    )
    return RedirectResponse(url="/", status_code=303)


@router.post("/ui/bookmarks/{bookmark_id}/delete")
def delete_bookmark(bookmark_id: int) -> RedirectResponse:
    bookmarks_router.delete_bookmark(bookmark_id)
    return RedirectResponse(url="/", status_code=303)


@router.get("/ui/digests", response_class=HTMLResponse)
def digests_page() -> HTMLResponse:
    digests = digests_router.list_digests(limit=20)
    return HTMLResponse(templates.digests_page(digests))


@router.post("/ui/digests/generate")
async def generate_digest(request: Request) -> RedirectResponse:
    form = await _form(request)
    period = form.get("period", "week")
    if period not in ("week", "month"):
        raise HTTPException(status_code=400, detail="invalid period")
    digests_router.generate(DigestCreate(period=period))
    return RedirectResponse(url="/ui/digests", status_code=303)
