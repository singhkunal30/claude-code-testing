from __future__ import annotations

from pydantic import BaseModel


class WeeklyCount(BaseModel):
    week_start: str  # ISO date (Monday)
    count: int


class Stats(BaseModel):
    total_entries: int
    entries_this_week: int
    current_streak_days: int
    longest_streak_days: int
    top_tags: dict[str, int]
    weekly_counts: list[WeeklyCount]
