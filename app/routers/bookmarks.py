from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.db import db_session
from app.models.bookmark import Bookmark, BookmarkCreate

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


def _set_tags(conn: sqlite3.Connection, bookmark_id: int, tag_names: list[str]) -> list[str]:
    resolved: list[str] = []
    for raw in tag_names:
        name = raw.strip().lower()
        if not name or name in resolved:
            continue
        conn.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (name,))
        tag_id = conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()["id"]
        conn.execute(
            "INSERT OR IGNORE INTO bookmark_tags(bookmark_id, tag_id) VALUES (?, ?)",
            (bookmark_id, tag_id),
        )
        resolved.append(name)
    return resolved


def _tags_for(conn: sqlite3.Connection, bookmark_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT t.name FROM tags t "
        "JOIN bookmark_tags bt ON bt.tag_id = t.id "
        "WHERE bt.bookmark_id = ? ORDER BY t.name",
        (bookmark_id,),
    ).fetchall()
    return [r["name"] for r in rows]


def _tags_for_many(conn: sqlite3.Connection, bookmark_ids: list[int]) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {i: [] for i in bookmark_ids}
    if not bookmark_ids:
        return out
    placeholders = ",".join("?" * len(bookmark_ids))
    rows = conn.execute(
        f"SELECT bt.bookmark_id, t.name FROM bookmark_tags bt "
        f"JOIN tags t ON t.id = bt.tag_id "
        f"WHERE bt.bookmark_id IN ({placeholders}) ORDER BY t.name",
        bookmark_ids,
    ).fetchall()
    for r in rows:
        out[r["bookmark_id"]].append(r["name"])
    return out


@router.post("", response_model=Bookmark, status_code=201)
def create_bookmark(payload: BookmarkCreate) -> Bookmark:
    now = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO bookmarks (url, title, notes, created_at) VALUES (?, ?, ?, ?)",
            (payload.url, payload.title, payload.notes, now),
        )
        new_id = cur.lastrowid
        _set_tags(conn, new_id, payload.tags or [])
        row = conn.execute("SELECT * FROM bookmarks WHERE id = ?", (new_id,)).fetchone()
        tags = _tags_for(conn, new_id)
    return Bookmark.from_row(row, tags)


@router.get("", response_model=list[Bookmark])
def list_bookmarks(
    tag: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
) -> list[Bookmark]:
    sql = "SELECT b.* FROM bookmarks b WHERE 1=1"
    params: list[object] = []
    if tag is not None:
        sql += (
            " AND b.id IN ("
            "  SELECT bt.bookmark_id FROM bookmark_tags bt "
            "  JOIN tags t ON t.id = bt.tag_id "
            "  WHERE t.name = ?"
            ")"
        )
        params.append(tag.strip().lower())
    sql += " ORDER BY b.created_at DESC LIMIT ?"
    params.append(limit)

    with db_session() as conn:
        rows = conn.execute(sql, params).fetchall()
        tags_by_id = _tags_for_many(conn, [r["id"] for r in rows])

    return [Bookmark.from_row(r, tags_by_id[r["id"]]) for r in rows]


@router.get("/{bookmark_id}", response_model=Bookmark)
def get_bookmark(bookmark_id: int) -> Bookmark:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Bookmark not found")
        tags = _tags_for(conn, bookmark_id)
    return Bookmark.from_row(row, tags)


@router.delete("/{bookmark_id}", status_code=204)
def delete_bookmark(bookmark_id: int) -> None:
    with db_session() as conn:
        cur = conn.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Bookmark not found")
