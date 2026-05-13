from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.db import db_session
from app.llm import auto_tag
from app.models.entry import Entry, EntryCreate

router = APIRouter(prefix="/entries", tags=["entries"])


def _set_tags(conn: sqlite3.Connection, entry_id: int, tag_names: list[str]) -> list[str]:
    """Upsert tag names and link them to entry_id. Returns the resolved tag names."""
    resolved: list[str] = []
    for raw in tag_names:
        name = raw.strip().lower()
        if not name or name in resolved:
            continue
        conn.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (name,))
        tag_id = conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()["id"]
        conn.execute(
            "INSERT OR IGNORE INTO entry_tags(entry_id, tag_id) VALUES (?, ?)",
            (entry_id, tag_id),
        )
        resolved.append(name)
    return resolved


def _tags_for(conn: sqlite3.Connection, entry_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT t.name FROM tags t "
        "JOIN entry_tags et ON et.tag_id = t.id "
        "WHERE et.entry_id = ? ORDER BY t.name",
        (entry_id,),
    ).fetchall()
    return [r["name"] for r in rows]


def _tags_for_many(conn: sqlite3.Connection, entry_ids: list[int]) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {i: [] for i in entry_ids}
    if not entry_ids:
        return out
    placeholders = ",".join("?" * len(entry_ids))
    rows = conn.execute(
        f"SELECT et.entry_id, t.name FROM entry_tags et "
        f"JOIN tags t ON t.id = et.tag_id "
        f"WHERE et.entry_id IN ({placeholders}) ORDER BY t.name",
        entry_ids,
    ).fetchall()
    for r in rows:
        out[r["entry_id"]].append(r["name"])
    return out


@router.post("", response_model=Entry, status_code=201)
def create_entry(payload: EntryCreate) -> Entry:
    tag_names = payload.tags if payload.tags is not None else auto_tag(payload.text)
    now = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO entries (text, source, created_at) VALUES (?, ?, ?)",
            (payload.text, payload.source, now),
        )
        new_id = cur.lastrowid
        _set_tags(conn, new_id, tag_names)
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (new_id,)).fetchone()
        tags = _tags_for(conn, new_id)
    return Entry.from_row(row, tags)


@router.get("", response_model=list[Entry])
def list_entries(
    tag: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    limit: int = Query(default=100, le=500),
) -> list[Entry]:
    sql = "SELECT e.* FROM entries e WHERE 1=1"
    params: list[object] = []
    if since is not None:
        sql += " AND e.created_at >= ?"
        params.append(since.isoformat())
    if tag is not None:
        sql += (
            " AND e.id IN ("
            "  SELECT et.entry_id FROM entry_tags et "
            "  JOIN tags t ON t.id = et.tag_id "
            "  WHERE t.name = ?"
            ")"
        )
        params.append(tag.strip().lower())
    sql += " ORDER BY e.created_at DESC LIMIT ?"
    params.append(limit)

    with db_session() as conn:
        rows = conn.execute(sql, params).fetchall()
        tags_by_id = _tags_for_many(conn, [r["id"] for r in rows])

    return [Entry.from_row(r, tags_by_id[r["id"]]) for r in rows]


@router.get("/tags/all", response_model=dict[str, int])
def list_tags() -> dict[str, int]:
    with db_session() as conn:
        rows = conn.execute(
            "SELECT t.name, COUNT(et.entry_id) AS c "
            "FROM tags t LEFT JOIN entry_tags et ON et.tag_id = t.id "
            "GROUP BY t.id HAVING c > 0 ORDER BY c DESC, t.name"
        ).fetchall()
    return {r["name"]: r["c"] for r in rows}


@router.get("/{entry_id}", response_model=Entry)
def get_entry(entry_id: int) -> Entry:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Entry not found")
        tags = _tags_for(conn, entry_id)
    return Entry.from_row(row, tags)


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: int) -> None:
    with db_session() as conn:
        cur = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entry not found")
