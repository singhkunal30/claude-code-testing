from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class Collection(BaseModel):
    id: int
    name: str
    description: str | None
    entry_ids: list[int]
    created_at: datetime
