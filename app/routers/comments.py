from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.models.comment import Comment, CommentCreate
from app.supabase import client

router = APIRouter(tags=["comments"])


def _to_comment(row: dict) -> Comment:
    created = row["created_at"]
    if isinstance(created, str):
        created = datetime.fromisoformat(created.replace("Z", "+00:00"))
    return Comment(
        id=row["id"],
        entry_id=row["entry_id"],
        parent_comment_id=row.get("parent_comment_id"),
        author=row.get("author"),
        body=row["body"],
        created_at=created,
        replies=[],
    )


def _build_tree(rows: list[dict]) -> list[Comment]:
    comments = [_to_comment(r) for r in rows]
    by_id: dict[int, Comment] = {c.id: c for c in comments}
    roots: list[Comment] = []
    for c in comments:
        if c.parent_comment_id is None or c.parent_comment_id not in by_id:
            roots.append(c)
        else:
            by_id[c.parent_comment_id].replies.append(c)
    return roots


def _ensure_entry(entry_id: int) -> None:
    rows = client().select("entries", filters={"id": ("eq", entry_id)})
    if not rows:
        raise HTTPException(status_code=404, detail="Entry not found")


@router.post("/entries/{entry_id}/comments", response_model=Comment, status_code=201)
def create_comment(entry_id: int, payload: CommentCreate) -> Comment:
    _ensure_entry(entry_id)
    sb = client()
    if payload.parent_comment_id is not None:
        parent = sb.select("comments", filters={"id": ("eq", payload.parent_comment_id)})
        if not parent or parent[0]["entry_id"] != entry_id:
            raise HTTPException(status_code=400, detail="Invalid parent_comment_id")
    [row] = sb.insert(
        "comments",
        {
            "entry_id": entry_id,
            "parent_comment_id": payload.parent_comment_id,
            "author": payload.author,
            "body": payload.body,
        },
    )
    return _to_comment(row)


@router.get("/entries/{entry_id}/comments", response_model=list[Comment])
def list_comments(entry_id: int) -> list[Comment]:
    _ensure_entry(entry_id)
    rows = client().select(
        "comments",
        filters={"entry_id": ("eq", entry_id)},
        order="created_at.asc",
    )
    return _build_tree(rows)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: int) -> None:
    removed = client().delete("comments", filters={"id": ("eq", comment_id)})
    if not removed:
        raise HTTPException(status_code=404, detail="Comment not found")
