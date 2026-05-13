from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PromptCreate(BaseModel):
    text: str = Field(min_length=1)
    active: bool = True


class Prompt(BaseModel):
    id: int
    text: str
    active: bool
    created_at: datetime
