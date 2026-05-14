from __future__ import annotations

import sqlite3
from datetime import datetime

from pydantic import BaseModel, Field


class EntryCreate(BaseModel):
    text: str = Field(min_length=1)
    source: str | None = None
    tags: list[str] | None = None


class Entry(BaseModel):
    id: int
    text: str
    source: str | None
    tags: list[str]
    created_at: datetime
    share_token: str | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row, tags: list[str]) -> "Entry":
        return cls(
            id=row["id"],
            text=row["text"],
            source=row["source"],
            tags=tags,
            created_at=datetime.fromisoformat(row["created_at"]),
        )
