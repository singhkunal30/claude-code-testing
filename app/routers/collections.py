from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.models.collection import Collection, CollectionCreate
from app.supabase import client

router = APIRouter(prefix="/collections", tags=["collections"])


def _entry_ids_for(collection_id: int) -> list[int]:
    links = client().select(
        "collection_entries",
        filters={"collection_id": ("eq", collection_id)},
    )
    return sorted(l["entry_id"] for l in links)


def _to_collection(row: dict, entry_ids: list[int]) -> Collection:
    created = row["created_at"]
    if isinstance(created, str):
        created = datetime.fromisoformat(created.replace("Z", "+00:00"))
    return Collection(
        id=row["id"],
        name=row["name"],
        description=row.get("description"),
        entry_ids=entry_ids,
        created_at=created,
    )


def _ensure_entry(entry_id: int) -> None:
    rows = client().select("entries", filters={"id": ("eq", entry_id)})
    if not rows:
        raise HTTPException(status_code=404, detail="Entry not found")


def _load_collection(collection_id: int) -> dict:
    rows = client().select("collections", filters={"id": ("eq", collection_id)})
    if not rows:
        raise HTTPException(status_code=404, detail="Collection not found")
    return rows[0]


@router.post("", response_model=Collection, status_code=201)
def create_collection(payload: CollectionCreate) -> Collection:
    sb = client()
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="name is required")
    if sb.select("collections", filters={"name": ("eq", name)}):
        raise HTTPException(status_code=409, detail="Collection name already exists")
    [row] = sb.insert("collections", {"name": name, "description": payload.description})
    return _to_collection(row, [])


@router.get("", response_model=list[Collection])
def list_collections() -> list[Collection]:
    rows = client().select("collections", order="created_at.desc")
    return [_to_collection(r, _entry_ids_for(r["id"])) for r in rows]


@router.get("/{collection_id}", response_model=Collection)
def get_collection(collection_id: int) -> Collection:
    row = _load_collection(collection_id)
    return _to_collection(row, _entry_ids_for(collection_id))


@router.delete("/{collection_id}", status_code=204)
def delete_collection(collection_id: int) -> None:
    removed = client().delete("collections", filters={"id": ("eq", collection_id)})
    if not removed:
        raise HTTPException(status_code=404, detail="Collection not found")


@router.post("/{collection_id}/entries/{entry_id}", response_model=Collection, status_code=201)
def add_entry(collection_id: int, entry_id: int) -> Collection:
    _load_collection(collection_id)
    _ensure_entry(entry_id)
    sb = client()
    sb.upsert(
        "collection_entries",
        {"collection_id": collection_id, "entry_id": entry_id},
        on_conflict="collection_id,entry_id",
    )
    row = _load_collection(collection_id)
    return _to_collection(row, _entry_ids_for(collection_id))


@router.delete("/{collection_id}/entries/{entry_id}", status_code=204)
def remove_entry(collection_id: int, entry_id: int) -> None:
    _load_collection(collection_id)
    removed = client().delete(
        "collection_entries",
        filters={"collection_id": ("eq", collection_id), "entry_id": ("eq", entry_id)},
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Entry not in collection")
