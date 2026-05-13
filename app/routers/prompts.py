from __future__ import annotations

import random
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.models.prompt import Prompt, PromptCreate
from app.supabase import client

router = APIRouter(prefix="/prompts", tags=["prompts"])


def _to_prompt(row: dict) -> Prompt:
    created = row["created_at"]
    if isinstance(created, str):
        created = datetime.fromisoformat(created.replace("Z", "+00:00"))
    return Prompt(
        id=row["id"],
        text=row["text"],
        active=row["active"],
        created_at=created,
    )


@router.post("", response_model=Prompt, status_code=201)
def create_prompt(payload: PromptCreate) -> Prompt:
    [row] = client().insert(
        "prompts",
        {"text": payload.text, "active": payload.active},
    )
    return _to_prompt(row)


@router.get("", response_model=list[Prompt])
def list_prompts(
    active: bool | None = Query(default=None),
    limit: int = Query(default=100, le=500),
) -> list[Prompt]:
    filters: dict = {}
    if active is not None:
        filters["active"] = ("eq", active)
    rows = client().select(
        "prompts",
        filters=filters,
        order="created_at.desc",
        limit=limit,
    )
    return [_to_prompt(r) for r in rows]


@router.get("/random", response_model=Prompt)
def random_prompt() -> Prompt:
    rows = client().select("prompts", filters={"active": ("eq", True)})
    if not rows:
        raise HTTPException(status_code=404, detail="No active prompts")
    return _to_prompt(random.choice(rows))


@router.get("/{prompt_id}", response_model=Prompt)
def get_prompt(prompt_id: int) -> Prompt:
    rows = client().select("prompts", filters={"id": ("eq", prompt_id)})
    if not rows:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return _to_prompt(rows[0])


@router.delete("/{prompt_id}", status_code=204)
def delete_prompt(prompt_id: int) -> None:
    removed = client().delete("prompts", filters={"id": ("eq", prompt_id)})
    if not removed:
        raise HTTPException(status_code=404, detail="Prompt not found")
