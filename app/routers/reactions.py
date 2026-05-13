from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.reaction import Reaction, ReactionCreate
from app.supabase import client

router = APIRouter(prefix="/entries/{entry_id}/reactions", tags=["reactions"])


def _ensure_entry(entry_id: int) -> None:
    rows = client().select("entries", filters={"id": ("eq", entry_id)})
    if not rows:
        raise HTTPException(status_code=404, detail="Entry not found")


def _list_reactions(entry_id: int) -> list[Reaction]:
    rows = client().select(
        "entry_reactions",
        filters={"entry_id": ("eq", entry_id)},
        order="emoji.asc",
    )
    return [Reaction(entry_id=r["entry_id"], emoji=r["emoji"], count=r["count"]) for r in rows]


@router.get("", response_model=list[Reaction])
def list_reactions(entry_id: int) -> list[Reaction]:
    _ensure_entry(entry_id)
    return _list_reactions(entry_id)


@router.post("", response_model=Reaction, status_code=201)
def react(entry_id: int, payload: ReactionCreate) -> Reaction:
    _ensure_entry(entry_id)
    sb = client()
    emoji = payload.emoji.strip()
    if not emoji:
        raise HTTPException(status_code=422, detail="emoji is required")
    existing = sb.select(
        "entry_reactions",
        filters={"entry_id": ("eq", entry_id), "emoji": ("eq", emoji)},
    )
    new_count = (existing[0]["count"] if existing else 0) + 1
    [row] = sb.upsert(
        "entry_reactions",
        {"entry_id": entry_id, "emoji": emoji, "count": new_count},
        on_conflict="entry_id,emoji",
    )
    return Reaction(entry_id=row["entry_id"], emoji=row["emoji"], count=row["count"])


@router.delete("/{emoji}", status_code=204)
def remove_reaction(entry_id: int, emoji: str) -> None:
    _ensure_entry(entry_id)
    removed = client().delete(
        "entry_reactions",
        filters={"entry_id": ("eq", entry_id), "emoji": ("eq", emoji)},
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Reaction not found")
