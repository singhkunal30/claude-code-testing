from fastapi import FastAPI

from app.routers import items

app = FastAPI(title="claude-code-testing", version="0.1.0")
app.include_router(items.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello from FastAPI"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
