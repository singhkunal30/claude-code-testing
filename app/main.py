from fastapi import FastAPI

from app.routers import (
    bookmarks,
    collections,
    comments,
    digests,
    entries,
    highlights,
    prompts,
    reactions,
)
from app.ui import router as ui_router

app = FastAPI(title="til-journal", version="0.1.0")
app.include_router(entries.router)
app.include_router(bookmarks.router)
app.include_router(digests.router)
app.include_router(reactions.router)
app.include_router(comments.router)
app.include_router(collections.router)
app.include_router(highlights.router)
app.include_router(prompts.router)
app.include_router(ui_router.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
