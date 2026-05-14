from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.base import User
from app.auth.session import current_user
from app.models.bookmark import Bookmark, BookmarkCreate
from app.supabase import client

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


def _normalize_tags(raw: list[str]) -> list[str]:
    seen: list[str] = []
    for name in raw:
        n = name.strip().lower()
        if n and n not in seen:
            seen.append(n)
    return seen


def _link_tags(bookmark_id: int, tag_names: list[str], user_id: str) -> list[str]:
    sb = client()
    if not tag_names:
        return []
    tag_rows = sb.upsert(
        "tags",
        [{"name": n, "user_id": user_id} for n in tag_names],
        on_conflict="user_id,name",
    )
    sb.insert(
        "bookmark_tags",
        [{"bookmark_id": bookmark_id, "tag_id": t["id"]} for t in tag_rows],
    )
    return _tags_for(bookmark_id)


def _tags_for(bookmark_id: int) -> list[str]:
    sb = client()
    links = sb.select("bookmark_tags", filters={"bookmark_id": ("eq", bookmark_id)})
    if not links:
        return []
    tag_rows = sb.select(
        "tags",
        filters={"id": ("in", [r["tag_id"] for r in links])},
        order="name.asc",
    )
    return [t["name"] for t in tag_rows]


def _tags_for_many(bookmark_ids: list[int]) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {i: [] for i in bookmark_ids}
    if not bookmark_ids:
        return out
    sb = client()
    links = sb.select("bookmark_tags", filters={"bookmark_id": ("in", bookmark_ids)})
    tag_ids = list({l["tag_id"] for l in links})
    if not tag_ids:
        return out
    tag_rows = sb.select("tags", filters={"id": ("in", tag_ids)})
    name_by_id = {t["id"]: t["name"] for t in tag_rows}
    for l in links:
        out[l["bookmark_id"]].append(name_by_id[l["tag_id"]])
    for k in out:
        out[k].sort()
    return out


def _own_bookmark(bookmark_id: int, user_id: str) -> dict:
    rows = client().select(
        "bookmarks",
        filters={"id": ("eq", bookmark_id), "user_id": ("eq", user_id)},
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return rows[0]


def _to_bookmark(row: dict, tags: list[str]) -> Bookmark:
    created = row["created_at"]
    if isinstance(created, str):
        created = datetime.fromisoformat(created.replace("Z", "+00:00"))
    return Bookmark(
        id=row["id"],
        url=row["url"],
        title=row.get("title"),
        notes=row.get("notes"),
        tags=tags,
        created_at=created,
    )


@router.post("", response_model=Bookmark, status_code=201)
def create_bookmark(
    payload: BookmarkCreate, user: User = Depends(current_user)
) -> Bookmark:
    sb = client()
    [row] = sb.insert(
        "bookmarks",
        {
            "user_id": user.id,
            "url": payload.url,
            "title": payload.title,
            "notes": payload.notes,
        },
    )
    tag_names = _normalize_tags(payload.tags or [])
    tags = _link_tags(row["id"], tag_names, user.id)
    return _to_bookmark(row, tags)


@router.get("", response_model=list[Bookmark])
def list_bookmarks(
    user: User = Depends(current_user),
    tag: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
) -> list[Bookmark]:
    sb = client()
    filters: dict = {"user_id": ("eq", user.id)}
    if tag is not None:
        tag_rows = sb.select(
            "tags",
            filters={"name": ("eq", tag.strip().lower()), "user_id": ("eq", user.id)},
        )
        if not tag_rows:
            return []
        link_rows = sb.select(
            "bookmark_tags", filters={"tag_id": ("eq", tag_rows[0]["id"])}
        )
        bookmark_ids = [l["bookmark_id"] for l in link_rows]
        if not bookmark_ids:
            return []
        filters["id"] = ("in", bookmark_ids)

    rows = sb.select("bookmarks", filters=filters, order="created_at.desc", limit=limit)
    tags_by_id = _tags_for_many([r["id"] for r in rows])
    return [_to_bookmark(r, tags_by_id[r["id"]]) for r in rows]


@router.get("/{bookmark_id}", response_model=Bookmark)
def get_bookmark(
    bookmark_id: int, user: User = Depends(current_user)
) -> Bookmark:
    row = _own_bookmark(bookmark_id, user.id)
    return _to_bookmark(row, _tags_for(bookmark_id))


@router.delete("/{bookmark_id}", status_code=204)
def delete_bookmark(
    bookmark_id: int, user: User = Depends(current_user)
) -> None:
    _own_bookmark(bookmark_id, user.id)
    client().delete("bookmarks", filters={"id": ("eq", bookmark_id)})
