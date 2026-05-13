from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    body: str = Field(min_length=1)
    author: str | None = None
    parent_comment_id: int | None = None


class Comment(BaseModel):
    id: int
    entry_id: int
    parent_comment_id: int | None
    author: str | None
    body: str
    created_at: datetime
    replies: list["Comment"] = []


Comment.model_rebuild()
