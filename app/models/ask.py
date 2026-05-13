from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.entry import Entry


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=20)


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[Entry]
