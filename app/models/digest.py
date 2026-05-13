from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


Period = Literal["week", "month"]


class DigestCreate(BaseModel):
    period: Period = "week"
    end_date: date | None = Field(default=None, description="Defaults to today UTC.")


class Digest(BaseModel):
    id: int
    period: Period
    start_date: date
    end_date: date
    content: str
    entry_ids: list[int]
    created_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Digest":
        return cls(
            id=row["id"],
            period=row["period"],
            start_date=date.fromisoformat(row["start_date"]),
            end_date=date.fromisoformat(row["end_date"]),
            content=row["content"],
            entry_ids=json.loads(row["entry_ids_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
