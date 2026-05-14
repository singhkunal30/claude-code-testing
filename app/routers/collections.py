from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.auth.base import User
from app.auth.session import current_user
from app.models.collection import Collection, CollectionCreate
from app.routers.entries import own_entry
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


def _own_collection(collection_id: int, user_id: str) -> dict:
    rows = client().select(
        "collections",
        filters={"id": ("eq", collection_id), "user_id": ("eq", user_id)},
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Collection not found")
    return rows[0]


@router.post("", response_model=Collection, status_code=201)
def create_collection(
    payload: CollectionCreate, user: User = Depends(current_user)
) -> Collection:
    sb = client()
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="name is required")
    if sb.select(
        "collections", filters={"name": ("eq", name), "user_id": ("eq", user.id)}
    ):
        raise HTTPException(status_code=409, detail="Collection name already exists")
    [row] = sb.insert(
        "collections",
        {"user_id": user.id, "name": name, "description": payload.description},
    )
    return _to_collection(row, [])


@router.get("", response_model=list[Collection])
def list_collections(user: User = Depends(current_user)) -> list[Collection]:
    rows = client().select(
        "collections",
        filters={"user_id": ("eq", user.id)},
        order="created_at.desc",
    )
    return [_to_collection(r, _entry_ids_for(r["id"])) for r in rows]


@router.get("/{collection_id}", response_model=Collection)
def get_collection(
    collection_id: int, user: User = Depends(current_user)
) -> Collection:
    row = _own_collection(collection_id, user.id)
    return _to_collection(row, _entry_ids_for(collection_id))


@router.delete("/{collection_id}", status_code=204)
def delete_collection(
    collection_id: int, user: User = Depends(current_user)
) -> None:
    _own_collection(collection_id, user.id)
    client().delete("collections", filters={"id": ("eq", collection_id)})


@router.post(
    "/{collection_id}/entries/{entry_id}", response_model=Collection, status_code=201
)
def add_entry(
    collection_id: int, entry_id: int, user: User = Depends(current_user)
) -> Collection:
    _own_collection(collection_id, user.id)
    own_entry(entry_id, user.id)
    sb = client()
    sb.upsert(
        "collection_entries",
        {"collection_id": collection_id, "entry_id": entry_id},
        on_conflict="collection_id,entry_id",
    )
    row = _own_collection(collection_id, user.id)
    return _to_collection(row, _entry_ids_for(collection_id))


@router.delete("/{collection_id}/entries/{entry_id}", status_code=204)
def remove_entry(
    collection_id: int, entry_id: int, user: User = Depends(current_user)
) -> None:
    _own_collection(collection_id, user.id)
    removed = client().delete(
        "collection_entries",
        filters={"collection_id": ("eq", collection_id), "entry_id": ("eq", entry_id)},
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Entry not in collection")
