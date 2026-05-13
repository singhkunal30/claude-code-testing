from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

from app.llm import generate_digest
from app.llm.base import DigestEntry, DigestInput
from app.models.digest import Digest, DigestCreate
from app.routers.entries import _tags_for_many
from app.supabase import client

router = APIRouter(prefix="/digests", tags=["digests"])


def _period_range(period: str, end: date) -> tuple[date, date]:
    if period == "week":
        return end - timedelta(days=6), end
    if period == "month":
        return end - timedelta(days=29), end
    raise HTTPException(status_code=400, detail=f"Unsupported period: {period}")


def _to_digest(row: dict) -> Digest:
    created = row["created_at"]
    if isinstance(created, str):
        created = datetime.fromisoformat(created.replace("Z", "+00:00"))
    entry_ids = row.get("entry_ids") or []
    if isinstance(entry_ids, str):
        import json

        entry_ids = json.loads(entry_ids)
    return Digest(
        id=row["id"],
        period=row["period"],
        start_date=date.fromisoformat(row["start_date"]) if isinstance(row["start_date"], str) else row["start_date"],
        end_date=date.fromisoformat(row["end_date"]) if isinstance(row["end_date"], str) else row["end_date"],
        content=row["content"],
        entry_ids=entry_ids,
        created_at=created,
    )


@router.post("/generate", response_model=Digest, status_code=201)
def generate(payload: DigestCreate) -> Digest:
    end = payload.end_date or datetime.now(timezone.utc).date()
    start, end = _period_range(payload.period, end)

    sb = client()
    rows = sb.select(
        "entries",
        filters={
            "created_at": ("gte", start.isoformat()),
        },
        order="created_at.asc",
        limit=500,
    )
    # Filter the upper bound client-side (PostgREST lte on date+time is fiddly)
    end_str = (end + timedelta(days=1)).isoformat()
    rows = [r for r in rows if (r["created_at"] if isinstance(r["created_at"], str) else r["created_at"].isoformat()) < end_str]

    tags_by_id = _tags_for_many([r["id"] for r in rows])
    entries = [
        DigestEntry(
            id=r["id"],
            text=r["text"],
            tags=tags_by_id[r["id"]],
            created_at=r["created_at"] if isinstance(r["created_at"], str) else r["created_at"].isoformat(),
        )
        for r in rows
    ]

    content = generate_digest(
        DigestInput(period=payload.period, start_date=start, end_date=end, entries=entries)
    )
    entry_ids = [e.id for e in entries]

    [row] = sb.insert(
        "digests",
        {
            "period": payload.period,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "content": content,
            "entry_ids": entry_ids,
        },
    )
    return _to_digest(row)


@router.get("", response_model=list[Digest])
def list_digests(limit: int = 50) -> list[Digest]:
    sb = client()
    rows = sb.select("digests", order="created_at.desc", limit=limit)
    return [_to_digest(r) for r in rows]


@router.get("/{digest_id}", response_model=Digest)
def get_digest(digest_id: int) -> Digest:
    sb = client()
    rows = sb.select("digests", filters={"id": ("eq", digest_id)})
    if not rows:
        raise HTTPException(status_code=404, detail="Digest not found")
    return _to_digest(rows[0])
