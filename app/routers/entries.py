from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.llm import auto_tag, embed
from app.models.entry import Entry, EntryCreate
from app.supabase import client

router = APIRouter(prefix="/entries", tags=["entries"])


def _normalize_tags(raw: list[str]) -> list[str]:
    seen: list[str] = []
    for name in raw:
        n = name.strip().lower()
        if n and n not in seen:
            seen.append(n)
    return seen


def _link_tags(entry_id: int, tag_names: list[str]) -> list[str]:
    """Upsert tag names, link them to entry_id, return resolved tag names."""
    sb = client()
    if not tag_names:
        return []
    tag_rows = sb.upsert(
        "tags",
        [{"name": n} for n in tag_names],
        on_conflict="name",
    )
    sb.insert("entry_tags", [{"entry_id": entry_id, "tag_id": t["id"]} for t in tag_rows])
    return _tags_for(entry_id)


def _tags_for(entry_id: int) -> list[str]:
    sb = client()
    links = sb.select("entry_tags", filters={"entry_id": ("eq", entry_id)})
    if not links:
        return []
    tag_rows = sb.select(
        "tags",
        filters={"id": ("in", [r["tag_id"] for r in links])},
        order="name.asc",
    )
    return [t["name"] for t in tag_rows]


def _tags_for_many(entry_ids: list[int]) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {i: [] for i in entry_ids}
    if not entry_ids:
        return out
    sb = client()
    links = sb.select("entry_tags", filters={"entry_id": ("in", entry_ids)})
    tag_ids = list({l["tag_id"] for l in links})
    if not tag_ids:
        return out
    tag_rows = sb.select("tags", filters={"id": ("in", tag_ids)})
    name_by_id = {t["id"]: t["name"] for t in tag_rows}
    grouped: dict[int, list[str]] = {i: [] for i in entry_ids}
    for l in links:
        grouped[l["entry_id"]].append(name_by_id[l["tag_id"]])
    for k in grouped:
        grouped[k].sort()
    return grouped


def _to_entry(row: dict, tags: list[str]) -> Entry:
    return Entry(
        id=row["id"],
        text=row["text"],
        source=row.get("source"),
        tags=tags,
        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        if isinstance(row["created_at"], str)
        else row["created_at"],
    )


@router.post("", response_model=Entry, status_code=201)
def create_entry(payload: EntryCreate) -> Entry:
    sb = client()
    raw_tags = payload.tags if payload.tags is not None else auto_tag(payload.text)
    tag_names = _normalize_tags(raw_tags)

    [row] = sb.insert(
        "entries",
        {
            "text": payload.text,
            "source": payload.source,
            "embedding": embed(payload.text),
        },
    )
    tags = _link_tags(row["id"], tag_names)
    return _to_entry(row, tags)


@router.get("", response_model=list[Entry])
def list_entries(
    tag: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    limit: int = Query(default=100, le=500),
) -> list[Entry]:
    sb = client()
    filters: dict = {}
    if since is not None:
        filters["created_at"] = ("gte", since.isoformat())

    if tag is not None:
        tag_rows = sb.select("tags", filters={"name": ("eq", tag.strip().lower())})
        if not tag_rows:
            return []
        link_rows = sb.select("entry_tags", filters={"tag_id": ("eq", tag_rows[0]["id"])})
        entry_ids = [l["entry_id"] for l in link_rows]
        if not entry_ids:
            return []
        filters["id"] = ("in", entry_ids)

    rows = sb.select("entries", filters=filters, order="created_at.desc", limit=limit)
    tags_by_id = _tags_for_many([r["id"] for r in rows])
    return [_to_entry(r, tags_by_id[r["id"]]) for r in rows]


@router.get("/search", response_model=list[Entry])
def search_entries(
    q: str = Query(min_length=1),
    limit: int = Query(default=50, le=500),
) -> list[Entry]:
    sb = client()
    needle = q.strip()
    if not needle:
        return []
    text_rows = sb.select(
        "entries",
        filters={"text": ("ilike", f"*{needle}*")},
        order="created_at.desc",
        limit=limit,
    )
    source_rows = sb.select(
        "entries",
        filters={"source": ("ilike", f"*{needle}*")},
        order="created_at.desc",
        limit=limit,
    )
    seen: dict[int, dict] = {}
    for r in text_rows + source_rows:
        seen.setdefault(r["id"], r)
    rows = sorted(
        seen.values(),
        key=lambda r: r["created_at"] if isinstance(r["created_at"], str) else r["created_at"].isoformat(),
        reverse=True,
    )[:limit]
    tags_by_id = _tags_for_many([r["id"] for r in rows])
    return [_to_entry(r, tags_by_id[r["id"]]) for r in rows]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))


def _embedding_for(row: dict) -> list[float]:
    vec = row.get("embedding")
    if isinstance(vec, list) and vec:
        return [float(v) for v in vec]
    # Backfill missing embeddings on read; the row may pre-date this feature.
    return embed(row["text"])


@router.get("/{entry_id}/related", response_model=list[Entry])
def related_entries(entry_id: int, k: int = Query(default=5, ge=1, le=50)) -> list[Entry]:
    sb = client()
    rows = sb.select("entries", filters={"id": ("eq", entry_id)})
    if not rows:
        raise HTTPException(status_code=404, detail="Entry not found")
    query_vec = _embedding_for(rows[0])

    all_rows = sb.select("entries", order="created_at.desc", limit=500)
    scored: list[tuple[float, dict]] = []
    for r in all_rows:
        if r["id"] == entry_id:
            continue
        scored.append((_cosine(query_vec, _embedding_for(r)), r))
    scored.sort(key=lambda kv: kv[0], reverse=True)
    top = [r for score, r in scored[:k] if score > 0]
    tags_by_id = _tags_for_many([r["id"] for r in top])
    return [_to_entry(r, tags_by_id[r["id"]]) for r in top]


@router.get("/tags/all", response_model=dict[str, int])
def list_tags() -> dict[str, int]:
    sb = client()
    links = sb.select("entry_tags")
    if not links:
        return {}
    tag_ids = list({l["tag_id"] for l in links})
    tag_rows = sb.select("tags", filters={"id": ("in", tag_ids)})
    name_by_id = {t["id"]: t["name"] for t in tag_rows}
    counts: dict[str, int] = {}
    for l in links:
        n = name_by_id[l["tag_id"]]
        counts[n] = counts.get(n, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


@router.get("/{entry_id}", response_model=Entry)
def get_entry(entry_id: int) -> Entry:
    sb = client()
    rows = sb.select("entries", filters={"id": ("eq", entry_id)})
    if not rows:
        raise HTTPException(status_code=404, detail="Entry not found")
    return _to_entry(rows[0], _tags_for(entry_id))


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: int) -> None:
    sb = client()
    removed = sb.delete("entries", filters={"id": ("eq", entry_id)})
    if not removed:
        raise HTTPException(status_code=404, detail="Entry not found")
