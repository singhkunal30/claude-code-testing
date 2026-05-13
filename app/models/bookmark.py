from __future__ import annotations

import sqlite3
from datetime import datetime

from pydantic import BaseModel, Field


class BookmarkCreate(BaseModel):
    url: str = Field(min_length=1)
    title: str | None = None
    notes: str | None = None
    tags: list[str] | None = None


class Bookmark(BaseModel):
    id: int
    url: str
    title: str | None
    notes: str | None
    tags: list[str]
    created_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row, tags: list[str]) -> "Bookmark":
        return cls(
            id=row["id"],
            url=row["url"],
            title=row["title"],
            notes=row["notes"],
            tags=tags,
            created_at=datetime.fromisoformat(row["created_at"]),
        )
