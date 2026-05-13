from fastapi import FastAPI

app = FastAPI(title="claude-code-testing", version="0.1.0")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello from FastAPI"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
