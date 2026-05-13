---
name: add-feature
description: Scaffold a new SQLite-backed resource for the TIL journal API. Creates a Pydantic model in app/models/, a router in app/routers/ with full CRUD endpoints, schema migration in app/db.py, and a pytest test file. Use when the user asks to add a new resource, table, or feature (e.g. "add a likes feature", "scaffold a bookmarks endpoint", "create a topics table"). Do not use when the user just wants a non-persistent in-memory router — this skill always creates a SQLite table.
---

# add-feature

Scaffolds a new SQLite-backed feature following this project's conventions.

## Inputs

Derive from the user's request:

- `resource_singular` — singular, lower-case (e.g. `bookmark`)
- `resource_plural` — plural, lower-case (e.g. `bookmarks`); URL prefix, router filename, table name
- `ModelName` — PascalCase singular (e.g. `Bookmark`)
- `fields` — additional columns beyond the standard `id` and `created_at`. If the user did not specify, default to a single `text: str` column and confirm with them.

If `fields` is unclear, ask once before scaffolding.

## Steps

1. **Add the schema.** Append a `CREATE TABLE IF NOT EXISTS {resource_plural} (...)` block to the `SCHEMA` constant in `app/db.py`. Always include `id INTEGER PRIMARY KEY AUTOINCREMENT` and `created_at TEXT NOT NULL`. Index columns that will be filtered on.

2. **Create the model** at `app/models/{resource_singular}.py`. Define `{ModelName}Create` (input) and `{ModelName}` (output, with `id`, `created_at`, and `from_row` classmethod). Follow the pattern in `app/models/entry.py`.

3. **Create the router** at `app/routers/{resource_plural}.py`. Provide `POST`, `GET` list, `GET /{id}`, `DELETE /{id}`. Use `db_session()` from `app.db`. Use modern type hints (`list[X]`, `dict[str, int]`, `X | None`).

4. **Wire the router** in `app/main.py`: add it to the imports near `entries, digests` and call `app.include_router({resource_plural}.router)`.

5. **Add tests** at `tests/test_{resource_plural}.py` — at minimum: create + read, list, get 404, delete. Use the existing `client` fixture from `tests/conftest.py` (it sets up an isolated SQLite DB per test).

6. **Run `uv run pytest tests/test_{resource_plural}.py -q`.** Do not mark this skill done if tests fail — fix the scaffold instead.

7. Report: list each file you created or edited.

## Conventions

- Migrations are append-only `CREATE TABLE IF NOT EXISTS` in `app/db.py`. Do not write a migration framework — this project relies on the idempotent SCHEMA.
- Routers must use `db_session()` (the context manager) — never open raw connections.
- Time fields are stored as ISO-8601 UTC strings; convert with `datetime.now(timezone.utc).isoformat()`.
- 404s use `HTTPException(status_code=404, detail="<ModelName> not found")`.

### Tags / list-of-strings columns

The project uses a relational pattern, not JSON columns:

- A shared `tags` table holds `(id, name UNIQUE)`.
- A per-resource link table — `<resource>_tags(<resource_id>, tag_id)` — with `FOREIGN KEY ... ON DELETE CASCADE` links resources to tags.
- Helper functions in `app/routers/entries.py` (`_set_tags`, `_tags_for`, `_tags_for_many`) show the canonical read/write pattern. Reuse the shared `tags` table; add a new link table per resource that needs tagging.
- Snapshot fields (e.g. `entry_ids` on `digests`) remain JSON-encoded TEXT (`<field>_json`) because they record a point-in-time list, not a live relation.

## Do not

- Do not introduce SQLAlchemy, SQLModel, or any ORM — the project deliberately uses stdlib `sqlite3`.
- Do not generate an LLM integration unless the user explicitly asks for one.
- Do not duplicate a table that already exists in `SCHEMA`.
