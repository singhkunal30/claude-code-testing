from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter

from app.models.stats import Stats, WeeklyCount
from app.supabase import client

router = APIRouter(tags=["stats"])


def _row_date(row: dict) -> date:
    created = row["created_at"]
    if isinstance(created, str):
        return datetime.fromisoformat(created.replace("Z", "+00:00")).astimezone(timezone.utc).date()
    if isinstance(created, datetime):
        return created.astimezone(timezone.utc).date() if created.tzinfo else created.date()
    return created  # already a date


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _streaks(dates: list[date], today: date) -> tuple[int, int]:
    if not dates:
        return 0, 0
    unique = sorted(set(dates))
    longest = current = 1
    for prev, curr in zip(unique, unique[1:]):
        if (curr - prev).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    last = unique[-1]
    if today - last > timedelta(days=1):
        current_streak = 0
    else:
        current_streak = 1
        for prev, curr in zip(reversed(unique[:-1]), reversed(unique)):
            if (curr - prev).days == 1:
                current_streak += 1
            else:
                break
    return current_streak, longest


@router.get("/stats", response_model=Stats)
def stats() -> Stats:
    sb = client()
    entry_rows = sb.select("entries", order="created_at.desc", limit=5000)

    today = datetime.now(timezone.utc).date()
    this_week_start = _week_start(today)
    dates = [_row_date(r) for r in entry_rows]
    entries_this_week = sum(1 for d in dates if d >= this_week_start)

    current_streak, longest_streak = _streaks(dates, today)

    counts_by_week: dict[date, int] = {
        this_week_start - timedelta(weeks=i): 0 for i in range(12)
    }
    for d in dates:
        wk = _week_start(d)
        if wk in counts_by_week:
            counts_by_week[wk] += 1
    weekly = [
        WeeklyCount(week_start=wk.isoformat(), count=c)
        for wk, c in sorted(counts_by_week.items())
    ]

    tag_links = sb.select("entry_tags")
    tag_rows = sb.select("tags") if tag_links else []
    name_by_id = {t["id"]: t["name"] for t in tag_rows}
    tag_counts: dict[str, int] = {}
    for link in tag_links:
        n = name_by_id.get(link["tag_id"])
        if n:
            tag_counts[n] = tag_counts.get(n, 0) + 1
    top_tags = dict(sorted(tag_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10])

    return Stats(
        total_entries=len(entry_rows),
        entries_this_week=entries_this_week,
        current_streak_days=current_streak,
        longest_streak_days=longest_streak,
        top_tags=top_tags,
        weekly_counts=weekly,
    )
