from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.db import init_db
from app.routers import digests, entries


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="til-journal", version="0.1.0", lifespan=lifespan)
app.include_router(entries.router)
app.include_router(digests.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "TIL journal API"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
