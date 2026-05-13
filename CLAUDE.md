# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

A FastAPI sandbox used to learn Claude Code features (hooks, skills, subagents, MCP, etc.) by building small endpoints and experiments.

## Stack

- Python 3.11
- FastAPI + Uvicorn
- `uv` for dependency and virtualenv management
- pytest + httpx for tests

## Layout

```
app/
  __init__.py
  main.py            # FastAPI app, top-level routes
  routers/           # Feature routers (one module per feature)
```

New endpoints that are larger than a single handler should go in their own router under `app/routers/` and be mounted from `app/main.py` via `app.include_router(...)`.

## Common commands

| Task            | Command                                          |
| --------------- | ------------------------------------------------ |
| Install deps    | `uv sync`                                        |
| Run dev server  | `uv run uvicorn app.main:app --reload`           |
| Run tests       | `uv run pytest`                                  |
| Add a dep       | `uv add <package>`                               |
| Add a dev dep   | `uv add --group dev <package>`                   |

## Conventions

- Type-hint all function signatures; prefer modern `dict[str, str]` style over `Dict`.
- Routes return plain dicts or Pydantic models — avoid `Response` unless headers/status need customizing.
- Keep handlers thin; push logic into helper functions or modules under `app/`.
- Tests live in `tests/` and use `httpx.AsyncClient` or `fastapi.testclient.TestClient`.

## Branching

Feature work happens on `claude/...` branches. The default working branch for ongoing experiments is `claude/explore-features-learning-llp1S`.
