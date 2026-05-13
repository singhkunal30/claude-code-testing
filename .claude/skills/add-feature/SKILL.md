---
name: add-feature
description: Scaffold a new Supabase-backed resource for the TIL journal API. Adds the SQL to supabase/schema.sql, creates a Pydantic model in app/models/, creates a router in app/routers/ that calls the Supabase HTTP client, and writes pytest tests using the in-memory Supabase fake. Use when the user asks to add a new resource, table, or feature (e.g. "add a likes feature", "scaffold a bookmarks endpoint", "create a topics table"). Do not use for non-persistent in-memory routers — this skill always creates a Supabase table.
---

# add-feature

Scaffolds a new Supabase-backed feature following this project's conventions.

## Inputs

Derive from the user's request:

- `resource_singular` — singular, lower-case (e.g. `bookmark`)
- `resource_plural` — plural, lower-case (e.g. `bookmarks`); URL prefix, router filename, table name
- `ModelName` — PascalCase singular (e.g. `Bookmark`)
- `fields` — additional columns beyond standard `id` and `created_at`. If not specified, default to a single `text TEXT NOT NULL` column and confirm with the user.
- `taggable` — whether the resource has tags (M2M). Default: yes.

If `fields` or `taggable` are unclear, ask once before scaffolding.

## Steps

1. **Append schema to `supabase/schema.sql`** — a `CREATE TABLE IF NOT EXISTS public.{resource_plural} (...)` block. Use `BIGSERIAL PRIMARY KEY` for `id` and `TIMESTAMPTZ NOT NULL DEFAULT now()` for `created_at`. If `taggable`, also add a `{resource_singular}_tags` link table with FK references and `ON DELETE CASCADE`, plus a tag index. Enable RLS on every new table (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`).

2. **Tell the user to re-run the schema in Supabase** — the file is the source of truth, but Supabase only knows what's already been run in its SQL editor. Mention this in the final report.

3. **Create the model** at `app/models/{resource_singular}.py` with `{ModelName}Create` (input) and `{ModelName}` (output). Output has `id`, optional fields, `tags: list[str]` if `taggable`, and `created_at: datetime`. No `from_row` classmethod — see existing models for the pattern.

4. **Create the router** at `app/routers/{resource_plural}.py` providing `POST`, `GET` list, `GET /{id}`, `DELETE /{id}`. Pattern:
   - Get the client via `from app.supabase import client`.
   - Call `client().insert / select / upsert / delete`.
   - If `taggable`, replicate the `_normalize_tags`, `_link_tags`, `_tags_for`, `_tags_for_many` pattern from `app/routers/entries.py` (with the table name swapped). Re-query tags via `_tags_for` after inserting so POST and GET return identical ordering.

5. **Wire the router** in `app/main.py`: add the import alongside `entries, bookmarks, digests` and `app.include_router({resource_plural}.router)`.

6. **If `taggable`, extend the in-memory fake** in `app/supabase.py`: add `"{resource_singular}_tags": ("{resource_singular}_id", "tag_id")` to `_InMemory._composite_pk`, and add an `ON DELETE CASCADE` clause to `_InMemory.delete` for the new resource's link table. Without this, tests will fail.

7. **Add tests** at `tests/test_{resource_plural}.py` covering at least: create + read, list (and tag filter if taggable), get 404, delete (and cascade if taggable). Use the existing `client` fixture from `tests/conftest.py` — it already resets the in-memory Supabase fake per test.

8. **Run `uv run pytest tests/test_{resource_plural}.py -q`.** Do not mark this skill done if tests fail — fix the scaffold instead.

9. Report: list each file you created or edited, AND remind the user to paste the updated `supabase/schema.sql` into the Supabase SQL editor and run it before hitting the new endpoints against the real DB.

## Conventions

- Schema in `supabase/schema.sql` is the source of truth. Append-only `CREATE TABLE IF NOT EXISTS`. Do not write a migration framework.
- Routers must not import `httpx`, `psycopg`, or `supabase` SDKs directly — call `app.supabase.client()`.
- Time fields are `TIMESTAMPTZ` server-side; in Python parse with `datetime.fromisoformat(value.replace("Z", "+00:00"))`.
- 404s use `HTTPException(status_code=404, detail="<ModelName> not found")`.
- The service_role key (`SUPABASE_KEY`) is used everywhere server-side; it bypasses RLS so no anon policies are needed.

### Tags (M2M)

- Shared `tags(id BIGSERIAL, name TEXT UNIQUE)` table — already in schema, reuse it.
- Per-resource link table `<resource>_tags(<resource>_id, tag_id)` with composite PK and `ON DELETE CASCADE` foreign keys.
- The `_normalize_tags` helper lowercases + de-duplicates input.
- `_link_tags` uses `client().upsert("tags", ..., on_conflict="name")` to get-or-create tag rows, then `client().insert("<resource>_tags", ...)` for links.
- `_tags_for` returns tags sorted by name (alphabetical) so POST/GET responses are consistent.

## Do not

- Do not introduce SQLAlchemy, SQLModel, asyncpg, psycopg, or supabase-py — the project goes through `app.supabase.client()` only.
- Do not generate an LLM integration unless the user explicitly asks for one.
- Do not duplicate a table that already exists in `supabase/schema.sql`.
- Do not forget to update `_InMemory._composite_pk` and the cascade logic in `app/supabase.py` when adding a taggable resource — the tests will silently pass but production behaviour will diverge.
