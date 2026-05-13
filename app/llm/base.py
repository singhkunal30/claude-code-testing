from __future__ import annotations

from datetime import date
from typing import Protocol

from pydantic import BaseModel


class DigestEntry(BaseModel):
    id: int
    text: str
    tags: list[str]
    created_at: str


class DigestInput(BaseModel):
    period: str
    start_date: date
    end_date: date
    entries: list[DigestEntry]


class LLMClient(Protocol):
    def tag(self, text: str) -> list[str]: ...
    def digest(self, payload: DigestInput) -> str: ...
