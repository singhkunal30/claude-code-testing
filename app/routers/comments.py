from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.auth.base import User
from app.auth.session import current_user
from app.models.comment import Comment, CommentCreate
from app.routers.entries import own_entry
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


@router.post("/entries/{entry_id}/comments", response_model=Comment, status_code=201)
def create_comment(
    entry_id: int,
    payload: CommentCreate,
    user: User = Depends(current_user),
) -> Comment:
    own_entry(entry_id, user.id)
    sb = client()
    if payload.parent_comment_id is not None:
        parent = sb.select(
            "comments",
            filters={"id": ("eq", payload.parent_comment_id), "user_id": ("eq", user.id)},
        )
        if not parent or parent[0]["entry_id"] != entry_id:
            raise HTTPException(status_code=400, detail="Invalid parent_comment_id")
    [row] = sb.insert(
        "comments",
        {
            "user_id": user.id,
            "entry_id": entry_id,
            "parent_comment_id": payload.parent_comment_id,
            "author": payload.author,
            "body": payload.body,
        },
    )
    return _to_comment(row)


@router.get("/entries/{entry_id}/comments", response_model=list[Comment])
def list_comments(
    entry_id: int, user: User = Depends(current_user)
) -> list[Comment]:
    own_entry(entry_id, user.id)
    rows = client().select(
        "comments",
        filters={"entry_id": ("eq", entry_id), "user_id": ("eq", user.id)},
        order="created_at.asc",
    )
    return _build_tree(rows)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: int, user: User = Depends(current_user)) -> None:
    sb = client()
    rows = sb.select(
        "comments",
        filters={"id": ("eq", comment_id), "user_id": ("eq", user.id)},
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Comment not found")
    sb.delete("comments", filters={"id": ("eq", comment_id)})
