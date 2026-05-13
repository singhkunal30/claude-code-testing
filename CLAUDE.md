# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

**TIL Journal API** — a FastAPI service for logging "today I learned" entries and producing periodic digests. Backed by **Supabase** (managed Postgres + auth) over its PostgREST HTTP API. Entries are auto-tagged via an LLM client; the project ships with a deterministic `FakeLLMClient` so it runs offline and without an LLM key.

## Stack

- Python 3.11
- FastAPI + Uvicorn
- **Supabase** (Postgres + PostgREST) accessed via `httpx` (no `supabase-py` SDK)
- Pydantic v2 for IO models
- pytest with an in-memory Supabase fake
- `uv` for dependency and virtualenv management

## Layout

```
app/
  __init__.py
  main.py              # FastAPI app, registers routers
  cli.py               # `python -m app.cli` for scheduled digest / stats
  config.py            # env-driven Settings (SUPABASE_URL, SUPABASE_KEY)
  supabase.py          # PostgREST client (_HttpClient) + in-memory fake (_InMemory)
  models/              # Pydantic models (one module per resource)
    entry.py
    bookmark.py
    digest.py
  routers/             # FastAPI routers (one module per resource)
    entries.py
    bookmarks.py
    digests.py
  llm/                 # LLM interface and clients
    base.py
    fake.py
    __init__.py
  ui/                  # Server-rendered HTML UI
    router.py
    templates.py
supabase/
  schema.sql           # Tables, indexes, RLS — paste into Supabase SQL editor
tests/
  conftest.py          # resets the in-memory Supabase fake per test
  test_entries.py
  test_bookmarks.py
  test_digests.py
  test_ui.py
  test_supabase_http.py  # verifies wire-format of real HTTP client
.claude/
  skills/
    add-feature/       # scaffold a new Supabase-backed resource
    log-til/           # log a TIL via the API path (writes through Supabase)
.env.example           # copy to .env, fill in real values
```

## Common commands

| Task             | Command                                          |
| ---------------- | ------------------------------------------------ |
| Install deps     | `uv sync`                                        |
| Run dev server   | `uv run uvicorn app.main:app --reload`           |
| Run tests        | `uv run pytest`                                  |
| Add a dep        | `uv add <package>`                               |
| Log a TIL        | invoke the `log-til` skill                       |
| Scaffold feature | invoke the `add-feature` skill                   |
| Weekly digest    | `uv run python -m app.cli digest --period week`  |
| DB stats         | `uv run python -m app.cli stats`                 |

## Setup

1. Create a Supabase project at supabase.com.
2. Copy `.env.example` to `.env` and fill in `SUPABASE_URL` and `SUPABASE_KEY` (the **service_role** secret — server-side only).
3. In the Supabase dashboard → SQL editor, paste `supabase/schema.sql` and run it.
4. `uv sync && uv run uvicorn app.main:app --reload`

## Conventions

- **All data access goes through `app.supabase.client()`**. Routers must not import `httpx` directly — they call `client().select / insert / upsert / delete`.
- **Use the service_role key** for server-side calls; it bypasses RLS. Never expose this key to a browser. Schema enables RLS but defines no anon policies, so anon writes are denied.
- **Time** is stored as `TIMESTAMPTZ` server-side. Python receives ISO-8601 strings; parse with `datetime.fromisoformat(...)`.
- **Tags** use a relational pattern: a shared `tags(id, name UNIQUE)` table plus per-resource link tables (`entry_tags`, `bookmark_tags`) with `ON DELETE CASCADE`. Helpers `_normalize_tags`, `_link_tags`, `_tags_for`, `_tags_for_many` in `app/routers/entries.py` are the canonical implementation.
- **Snapshot lists** (e.g. `entry_ids` on `digests`) are stored as `JSONB` columns because they record a point-in-time list, not a live relation.
- **Type hints** use the modern style: `list[X]`, `dict[str, int]`, `X | None`.
- **LLM access** goes through `app.llm.auto_tag` and `app.llm.generate_digest`. Swap clients with `app.llm.set_client(...)`.
- **404s** raise `HTTPException(status_code=404, detail="<ModelName> not found")`.
- **UI routes** live in `app/ui/router.py`, are HTML-only, `include_in_schema=False`. Forms are parsed via stdlib `urllib.parse.parse_qs` — do not add `python-multipart`.
- **Tests** call `reset_for_tests()` (via the `client` fixture) which swaps in a fresh in-memory Supabase fake. Tests never touch the real Supabase.
- **For the real HTTP path**, the wire-format is locked down in `tests/test_supabase_http.py` using `httpx.MockTransport`.

## Branching

Feature work happens on `claude/...` branches. The default working branch is `claude/explore-features-learning-llp1S`.

## Future work / not done yet

- Real `AnthropicLLMClient` implementing `LLMClient`.
- Auth on UI + API using Supabase Auth (GoTrue) and the `anon` key path.
- Webhook ingest from external sources.
- Tag editing (rename, merge) UI.
- Replace multi-call composition in routers with PostgREST embedded selects (`?select=*,tags(name)`) once the in-memory fake supports embeds.
