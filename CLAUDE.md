# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

**TIL Journal API** — a FastAPI service for logging "today I learned" entries and producing periodic digests. Entries are auto-tagged via an LLM client; the project ships with a deterministic `FakeLLMClient` so it runs offline and without an API key.

## Stack

- Python 3.11
- FastAPI + Uvicorn
- Stdlib `sqlite3` (no ORM — deliberate; see Conventions)
- Pydantic v2 for IO models
- pytest + httpx for tests
- `uv` for dependency and virtualenv management

## Layout

```
app/
  __init__.py
  main.py              # FastAPI app, lifespan calls init_db()
  db.py                # sqlite3 connection helper, SCHEMA, init_db()
  models/              # Pydantic models (one module per resource)
    entry.py
    digest.py
  routers/             # FastAPI routers (one module per resource)
    entries.py
    digests.py
  llm/                 # LLM interface and clients
    base.py            # LLMClient protocol + DigestInput / DigestEntry
    fake.py            # FakeLLMClient (default, offline, deterministic)
    __init__.py        # set_client / get_client / auto_tag / generate_digest
tests/
  conftest.py          # `client` fixture with isolated per-test sqlite DB
  test_entries.py
  test_digests.py
.claude/
  skills/
    add-feature/       # scaffold a new SQLite-backed resource
    log-til/           # log a TIL directly into the DB
```

## Common commands

| Task            | Command                                          |
| --------------- | ------------------------------------------------ |
| Install deps    | `uv sync`                                        |
| Run dev server  | `uv run uvicorn app.main:app --reload`           |
| Run tests       | `uv run pytest`                                  |
| Add a dep       | `uv add <package>`                               |
| Log a TIL       | invoke the `log-til` skill                       |
| Scaffold feature| invoke the `add-feature` skill                   |

## Conventions

- **No ORM.** Use stdlib `sqlite3` directly. Always go through `app.db.db_session()` (a context manager that commits on success, rolls back on exception).
- **Schema lives in `app/db.py`** as a single `SCHEMA` string of `CREATE TABLE IF NOT EXISTS` statements. Append new tables there — do not add a migrations framework.
- **Time** is stored as ISO-8601 UTC strings (`datetime.now(timezone.utc).isoformat()`).
- **List columns** (tags, entry_ids) are stored as JSON-encoded TEXT columns named `<field>_json`; decode in the model's `from_row` classmethod.
- **Type hints** use the modern style: `list[X]`, `dict[str, int]`, `X | None`.
- **LLM access** goes through `app.llm.auto_tag` and `app.llm.generate_digest`. To swap in a real client, call `app.llm.set_client(...)` once at startup.
- **404s** raise `HTTPException(status_code=404, detail="<ModelName> not found")`.
- **Tests** use the `client` fixture from `tests/conftest.py` which sets `TIL_DB_PATH` to a tmp file. Never write to the dev DB from a test.

## Branching

Feature work happens on `claude/...` branches. The default working branch is `claude/explore-features-learning-llp1S`.

## Future work / not done yet

- Real `AnthropicLLMClient` implementing `LLMClient`.
- Many-to-many tags table (currently JSON column).
- Auth.
- Webhook ingest from external sources.
