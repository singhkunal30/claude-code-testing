from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

from app.db import db_session
from app.llm import generate_digest
from app.llm.base import DigestEntry, DigestInput
from app.models.digest import Digest, DigestCreate

router = APIRouter(prefix="/digests", tags=["digests"])


def _period_range(period: str, end: date) -> tuple[date, date]:
    if period == "week":
        return end - timedelta(days=6), end
    if period == "month":
        return end - timedelta(days=29), end
    raise HTTPException(status_code=400, detail=f"Unsupported period: {period}")


@router.post("/generate", response_model=Digest, status_code=201)
def generate(payload: DigestCreate) -> Digest:
    end = payload.end_date or datetime.now(timezone.utc).date()
    start, end = _period_range(payload.period, end)

    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM entries WHERE date(created_at) BETWEEN ? AND ? "
            "ORDER BY created_at ASC",
            (start.isoformat(), end.isoformat()),
        ).fetchall()

        entries = [
            DigestEntry(
                id=r["id"],
                text=r["text"],
                tags=json.loads(r["tags_json"]),
                created_at=r["created_at"],
            )
            for r in rows
        ]

        content = generate_digest(
            DigestInput(period=payload.period, start_date=start, end_date=end, entries=entries)
        )
        now = datetime.now(timezone.utc).isoformat()
        entry_ids = [e.id for e in entries]

        cur = conn.execute(
            "INSERT INTO digests (period, start_date, end_date, content, entry_ids_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                payload.period,
                start.isoformat(),
                end.isoformat(),
                content,
                json.dumps(entry_ids),
                now,
            ),
        )
        new_id = cur.lastrowid
        row = conn.execute("SELECT * FROM digests WHERE id = ?", (new_id,)).fetchone()

    return Digest.from_row(row)


@router.get("", response_model=list[Digest])
def list_digests(limit: int = 50) -> list[Digest]:
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM digests ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [Digest.from_row(r) for r in rows]


@router.get("/{digest_id}", response_model=Digest)
def get_digest(digest_id: int) -> Digest:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM digests WHERE id = ?", (digest_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Digest not found")
    return Digest.from_row(row)
