"""HTML UI for the TIL journal. Form-driven, no JS framework.

Parses application/x-www-form-urlencoded bodies via stdlib urllib.parse
(no python-multipart dependency).
"""
from __future__ import annotations

import urllib.parse

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.models.ask import AskRequest
from app.models.bookmark import BookmarkCreate
from app.models.digest import DigestCreate
from app.models.entry import EntryCreate
from app.models.highlight import HighlightCreate
from app.models.reaction import Reaction, ReactionCreate
from app.routers import ask as ask_router
from app.routers import bookmarks as bookmarks_router
from app.routers import digests as digests_router
from app.routers import entries as entries_router
from app.routers import highlights as highlights_router
from app.routers import prompts as prompts_router
from app.routers import reactions as reactions_router
from app.routers import share as share_router
from app.routers import stats as stats_router
from app.supabase import client
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


def _reactions_by_entry(entry_ids: list[int]) -> dict[int, list[Reaction]]:
    if not entry_ids:
        return {}
    rows = client().select(
        "entry_reactions",
        filters={"entry_id": ("in", entry_ids)},
    )
    out: dict[int, list[Reaction]] = {i: [] for i in entry_ids}
    for r in rows:
        out[r["entry_id"]].append(
            Reaction(entry_id=r["entry_id"], emoji=r["emoji"], count=r["count"])
        )
    return out


def _highlighted_ids(entry_ids: list[int]) -> set[int]:
    if not entry_ids:
        return set()
    rows = client().select(
        "highlights",
        filters={"entry_id": ("in", entry_ids)},
    )
    return {r["entry_id"] for r in rows}


def _random_prompt_text() -> str | None:
    try:
        return prompts_router.random_prompt().text
    except HTTPException:
        return None


@router.get("/", response_class=HTMLResponse)
def home(q: str | None = Query(default=None)) -> HTMLResponse:
    if q and q.strip():
        entries = entries_router.search_entries(q=q.strip(), limit=20)
    else:
        entries = entries_router.list_entries(tag=None, since=None, limit=20)
    bookmarks = bookmarks_router.list_bookmarks(tag=None, limit=20)
    entry_ids = [e.id for e in entries]
    return HTMLResponse(
        templates.home(
            entries=entries,
            bookmarks=bookmarks,
            reactions_by_entry=_reactions_by_entry(entry_ids),
            highlighted_ids=_highlighted_ids(entry_ids),
            daily_prompt=_random_prompt_text(),
            q=q or "",
        )
    )


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


@router.post("/ui/entries/{entry_id}/react")
async def react(entry_id: int, request: Request) -> RedirectResponse:
    form = await _form(request)
    emoji = form.get("emoji", "").strip()
    if not emoji:
        raise HTTPException(status_code=400, detail="emoji required")
    reactions_router.react(entry_id, ReactionCreate(emoji=emoji))
    return RedirectResponse(url="/", status_code=303)


@router.post("/ui/entries/{entry_id}/highlight")
def toggle_highlight(entry_id: int) -> RedirectResponse:
    existing = client().select("highlights", filters={"entry_id": ("eq", entry_id)})
    if existing:
        for h in existing:
            highlights_router.delete_highlight(h["id"])
    else:
        highlights_router.create_highlight(HighlightCreate(entry_id=entry_id))
    return RedirectResponse(url="/", status_code=303)


@router.post("/ui/entries/{entry_id}/share/toggle")
def toggle_share(entry_id: int) -> RedirectResponse:
    row = client().select("entries", filters={"id": ("eq", entry_id)})
    if not row:
        raise HTTPException(status_code=404, detail="Entry not found")
    if row[0].get("share_token"):
        share_router.disable_share(entry_id)
    else:
        share_router.enable_share(entry_id)
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


@router.get("/ui/stats", response_class=HTMLResponse)
def stats_page() -> HTMLResponse:
    return HTMLResponse(templates.stats_page(stats_router.stats()))


@router.get("/ui/ask", response_class=HTMLResponse)
def ask_page() -> HTMLResponse:
    return HTMLResponse(templates.ask_page())


@router.post("/ui/ask", response_class=HTMLResponse)
async def ask_submit(request: Request) -> HTMLResponse:
    form = await _form(request)
    question = form.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question required")
    result = ask_router.ask(AskRequest(question=question, k=5))
    return HTMLResponse(
        templates.ask_page(question=question, answer=result.answer, sources=result.sources)
    )


@router.get("/share/{token}", response_class=HTMLResponse)
def share_view(token: str) -> HTMLResponse:
    sb = client()
    rows = sb.select("entries", filters={"share_token": ("eq", token)})
    if not rows:
        raise HTTPException(status_code=404, detail="Shared entry not found")
    row = rows[0]
    tags = entries_router._tags_for(row["id"])
    entry = entries_router._to_entry(row, tags)
    return HTMLResponse(templates.share_view(entry))
