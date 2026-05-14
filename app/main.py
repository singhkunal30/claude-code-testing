from fastapi import FastAPI

from app.routers import (
    ask,
    bookmarks,
    collections,
    comments,
    digests,
    entries,
    export,
    highlights,
    prompts,
    reactions,
    share,
    stats,
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
app.include_router(ask.router)
app.include_router(stats.router)
app.include_router(share.router)
app.include_router(export.router)
app.include_router(ui_router.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
