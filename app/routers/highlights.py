from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.models.highlight import Highlight, HighlightCreate
from app.supabase import client

router = APIRouter(prefix="/highlights", tags=["highlights"])


def _to_highlight(row: dict) -> Highlight:
    created = row["created_at"]
    if isinstance(created, str):
        created = datetime.fromisoformat(created.replace("Z", "+00:00"))
    return Highlight(
        id=row["id"],
        entry_id=row["entry_id"],
        note=row.get("note"),
        created_at=created,
    )


@router.post("", response_model=Highlight, status_code=201)
def create_highlight(payload: HighlightCreate) -> Highlight:
    sb = client()
    if not sb.select("entries", filters={"id": ("eq", payload.entry_id)}):
        raise HTTPException(status_code=404, detail="Entry not found")
    [row] = sb.insert(
        "highlights",
        {"entry_id": payload.entry_id, "note": payload.note},
    )
    return _to_highlight(row)


@router.get("", response_model=list[Highlight])
def list_highlights(
    entry_id: int | None = Query(default=None),
    limit: int = Query(default=100, le=500),
) -> list[Highlight]:
    filters: dict = {}
    if entry_id is not None:
        filters["entry_id"] = ("eq", entry_id)
    rows = client().select(
        "highlights",
        filters=filters,
        order="created_at.desc",
        limit=limit,
    )
    return [_to_highlight(r) for r in rows]


@router.get("/{highlight_id}", response_model=Highlight)
def get_highlight(highlight_id: int) -> Highlight:
    rows = client().select("highlights", filters={"id": ("eq", highlight_id)})
    if not rows:
        raise HTTPException(status_code=404, detail="Highlight not found")
    return _to_highlight(rows[0])


@router.delete("/{highlight_id}", status_code=204)
def delete_highlight(highlight_id: int) -> None:
    removed = client().delete("highlights", filters={"id": ("eq", highlight_id)})
    if not removed:
        raise HTTPException(status_code=404, detail="Highlight not found")
