from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.db import db_session
from app.llm import auto_tag
from app.models.entry import Entry, EntryCreate

router = APIRouter(prefix="/entries", tags=["entries"])


@router.post("", response_model=Entry, status_code=201)
def create_entry(payload: EntryCreate) -> Entry:
    tags = payload.tags if payload.tags is not None else auto_tag(payload.text)
    now = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO entries (text, source, tags_json, created_at) VALUES (?, ?, ?, ?)",
            (payload.text, payload.source, json.dumps(tags), now),
        )
        new_id = cur.lastrowid
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (new_id,)).fetchone()
    return Entry.from_row(row)


@router.get("", response_model=list[Entry])
def list_entries(
    tag: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    limit: int = Query(default=100, le=500),
) -> list[Entry]:
    sql = "SELECT * FROM entries WHERE 1=1"
    params: list[object] = []
    if since is not None:
        sql += " AND created_at >= ?"
        params.append(since.isoformat())
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with db_session() as conn:
        rows = conn.execute(sql, params).fetchall()

    entries = [Entry.from_row(r) for r in rows]
    if tag is not None:
        entries = [e for e in entries if tag in e.tags]
    return entries


@router.get("/{entry_id}", response_model=Entry)
def get_entry(entry_id: int) -> Entry:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return Entry.from_row(row)


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: int) -> None:
    with db_session() as conn:
        cur = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entry not found")


@router.get("/tags/all", response_model=dict[str, int])
def list_tags() -> dict[str, int]:
    counts: dict[str, int] = {}
    with db_session() as conn:
        rows = conn.execute("SELECT tags_json FROM entries").fetchall()
    for r in rows:
        for t in json.loads(r["tags_json"]):
            counts[t] = counts.get(t, 0) + 1
    return counts
