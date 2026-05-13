from __future__ import annotations

from pydantic import BaseModel, Field


class ReactionCreate(BaseModel):
    emoji: str = Field(min_length=1, max_length=32)


class Reaction(BaseModel):
    entry_id: int
    emoji: str
    count: int
