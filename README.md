# claude-code-testing

A FastAPI sandbox for exploring Claude Code features.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management

## Setup

```bash
uv sync
```

## Run

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at http://127.0.0.1:8000.
Interactive docs: http://127.0.0.1:8000/docs.

## Endpoints

- `GET /` — hello message
- `GET /health` — health check

## Tests

```bash
uv run pytest
```
