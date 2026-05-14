from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from app.auth.base import User
from app.auth.session import current_user
from app.routers.entries import _tags_for_many, _to_entry
from app.supabase import client

router = APIRouter(tags=["export"])


@router.get("/export.json")
def export_json(user: User = Depends(current_user)) -> list[dict]:
    sb = client()
    rows = sb.select(
        "entries",
        filters={"user_id": ("eq", user.id)},
        order="created_at.desc",
        limit=5000,
    )
    tags_by_id = _tags_for_many([r["id"] for r in rows])
    return [
        _to_entry(r, tags_by_id[r["id"]]).model_dump(mode="json", exclude={"share_token"})
        for r in rows
    ]


@router.get("/export.md", response_class=PlainTextResponse)
def export_markdown(user: User = Depends(current_user)) -> PlainTextResponse:
    sb = client()
    rows = sb.select(
        "entries",
        filters={"user_id": ("eq", user.id)},
        order="created_at.desc",
        limit=5000,
    )
    tags_by_id = _tags_for_many([r["id"] for r in rows])
    entries = [_to_entry(r, tags_by_id[r["id"]]) for r in rows]

    by_day: dict[str, list] = {}
    for e in entries:
        day = e.created_at.date().isoformat()
        by_day.setdefault(day, []).append(e)

    lines = [
        "# TIL Journal",
        f"_Exported {datetime.now(timezone.utc).date().isoformat()} — {len(entries)} entries_",
        "",
    ]
    for day in sorted(by_day.keys(), reverse=True):
        lines.append(f"## {day}")
        lines.append("")
        for e in by_day[day]:
            tagstr = f" _[{', '.join(e.tags)}]_" if e.tags else ""
            src = f" — [source]({e.source})" if e.source else ""
            lines.append(f"- {e.text}{tagstr}{src}")
        lines.append("")
    return PlainTextResponse(
        "\n".join(lines),
        headers={"Content-Disposition": 'attachment; filename="til-journal.md"'},
        media_type="text/markdown; charset=utf-8",
    )
