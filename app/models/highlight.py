from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HighlightCreate(BaseModel):
    entry_id: int = Field(gt=0)
    note: str | None = None


class Highlight(BaseModel):
    id: int
    entry_id: int
    note: str | None
    created_at: datetime
