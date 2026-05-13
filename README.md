# TIL Journal API

A small FastAPI service for logging "today I learned" entries and generating periodic digests. Backed by **Supabase** (managed Postgres). Entries are auto-tagged by an offline LLM fake; swap in a real client by setting `app.llm.set_client(...)`.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management
- A free Supabase project

## Setup

### 1. Supabase project (~3 min)

1. Create a project at https://supabase.com.
2. Wait for it to spin up.
3. Go to **Settings → API** and copy:
   - **Project URL** → `SUPABASE_URL`
   - **service_role secret** → `SUPABASE_KEY` (server-only — do not expose to browsers)
4. Go to **SQL editor → New query**, paste the contents of `supabase/schema.sql`, and Run.

### 2. Local environment

```bash
cp .env.example .env
# Edit .env, paste SUPABASE_URL and SUPABASE_KEY
uv sync
```

### 3. Run

```bash
uv run uvicorn app.main:app --reload
```

- Web UI: http://127.0.0.1:8000/
- Interactive API docs: http://127.0.0.1:8000/docs

### 4. Tests

```bash
uv run pytest
```

Tests use an in-memory Supabase fake and a `MockTransport` for the HTTP client — no network, no real Supabase needed.

## Endpoints

### Entries

- `POST /entries` — log a TIL. Auto-tags if `tags` is omitted.
- `GET /entries?tag=<tag>&since=<iso8601>` — list.
- `GET /entries/{id}` / `DELETE /entries/{id}`.
- `GET /entries/tags/all` — counts per tag.

### Bookmarks

- `POST /bookmarks` — save a URL with optional `title`, `notes`, `tags`.
- `GET /bookmarks?tag=<tag>` — list.
- `GET /bookmarks/{id}` / `DELETE /bookmarks/{id}`.

### Digests

- `POST /digests/generate` body `{"period": "week" | "month", "end_date"?: "YYYY-MM-DD"}`.
- `GET /digests` — list recent digests.
- `GET /digests/{id}`.

## CLI

```bash
uv run python -m app.cli stats
uv run python -m app.cli digest --period week
uv run python -m app.cli digest --period month
```

Pair with cron for automatic weekly digests.

## Claude Code skills

In `.claude/skills/`:

- **`add-feature`** — scaffold a new Supabase-backed resource (model, router, schema, tests) following project conventions.
- **`log-til`** — log a TIL from a Claude Code session by invoking the API path directly. Requires `SUPABASE_URL` and `SUPABASE_KEY` set in the env.

## Deployment

Any platform that runs a Python web app works (Fly.io, Render, Hugging Face Spaces, Railway, etc.). Set `SUPABASE_URL` and `SUPABASE_KEY` as platform secrets. Bind `uvicorn` to `0.0.0.0` and the platform's injected `$PORT`.
