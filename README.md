# TIL Journal API

A small FastAPI service for logging "today I learned" entries and generating periodic digests. Entries are auto-tagged by an LLM client; ships with a deterministic offline fake so it runs without an API key.

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

- Web UI: http://127.0.0.1:8000/
- Interactive API docs: http://127.0.0.1:8000/docs

## Tests

```bash
uv run pytest
```

## Endpoints

### Entries

- `POST /entries` — log a TIL. Auto-tags if `tags` is omitted.
  ```bash
  curl -X POST http://127.0.0.1:8000/entries \
    -H 'content-type: application/json' \
    -d '{"text": "FastAPI lifespan handlers replace startup/shutdown events"}'
  ```
- `GET /entries?tag=<tag>&since=<iso8601>` — list entries.
- `GET /entries/{id}` — fetch one.
- `DELETE /entries/{id}` — delete.
- `GET /entries/tags/all` — counts per tag.

### Bookmarks

- `POST /bookmarks` — save a URL with optional `title`, `notes`, `tags`.
- `GET /bookmarks?tag=<tag>` — list.
- `GET /bookmarks/{id}` / `DELETE /bookmarks/{id}` — read / delete.

### Digests

- `POST /digests/generate` body `{"period": "week" | "month", "end_date"?: "YYYY-MM-DD"}` — generate a digest covering the period ending on `end_date` (default today).
- `GET /digests` — list recent digests.
- `GET /digests/{id}` — fetch one.

## CLI

```bash
uv run python -m app.cli stats                       # entry/digest counts
uv run python -m app.cli digest --period week        # generate + print digest
uv run python -m app.cli digest --period month       # 30-day digest
```

Pair with cron for automatic weekly digests.

## Configuration

| Env var        | Default                     | Purpose                          |
| -------------- | --------------------------- | -------------------------------- |
| `TIL_DB_PATH`  | `<repo>/til.db`             | Path to the SQLite database.     |

## Claude Code skills

This repo ships with two skills (in `.claude/skills/`) that Claude Code can auto-discover:

- **`add-feature`** — scaffolds a new SQLite-backed resource (model, router, schema, tests).
- **`log-til`** — log a TIL directly from a Claude Code session; bypasses HTTP and writes to the local DB.
