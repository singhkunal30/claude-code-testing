from __future__ import annotations

import json
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

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Entry":
        return cls(
            id=row["id"],
            text=row["text"],
            source=row["source"],
            tags=json.loads(row["tags_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
