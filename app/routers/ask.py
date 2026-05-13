from __future__ import annotations

from fastapi import APIRouter

from app.llm import answer, embed
from app.llm.base import DigestEntry
from app.models.ask import AskRequest, AskResponse
from app.routers.entries import _cosine, _embedding_for, _tags_for_many, _to_entry
from app.supabase import client

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    sb = client()
    query_vec = embed(payload.question)
    all_rows = sb.select("entries", order="created_at.desc", limit=500)

    scored = [(_cosine(query_vec, _embedding_for(r)), r) for r in all_rows]
    scored.sort(key=lambda kv: kv[0], reverse=True)
    top_rows = [r for score, r in scored[: payload.k] if score > 0]

    tags_by_id = _tags_for_many([r["id"] for r in top_rows])
    sources = [_to_entry(r, tags_by_id[r["id"]]) for r in top_rows]

    digest_entries = [
        DigestEntry(
            id=r["id"],
            text=r["text"],
            tags=tags_by_id[r["id"]],
            created_at=r["created_at"]
            if isinstance(r["created_at"], str)
            else r["created_at"].isoformat(),
        )
        for r in top_rows
    ]
    return AskResponse(
        question=payload.question,
        answer=answer(payload.question, digest_entries),
        sources=sources,
    )
