from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/items", tags=["items"])


class ItemIn(BaseModel):
    name: str


class Item(ItemIn):
    id: int


# TODO: replace with real persistence
_store: dict[int, Item] = {}
_next_id: int = 1


@router.get("", response_model=list[Item])
def list_items() -> list[Item]:
    return list(_store.values())


@router.post("", response_model=Item, status_code=201)
def create_item(payload: ItemIn) -> Item:
    global _next_id
    obj = Item(id=_next_id, **payload.model_dump())
    _store[_next_id] = obj
    _next_id += 1
    return obj


@router.get("/{item_id}", response_model=Item)
def get_item(item_id: int) -> Item:
    obj = _store.get(item_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return obj


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int) -> None:
    if item_id not in _store:
        raise HTTPException(status_code=404, detail="Item not found")
    del _store[item_id]
