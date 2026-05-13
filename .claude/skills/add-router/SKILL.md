---
name: add-router
description: Scaffold a new FastAPI router with CRUD-shaped endpoints, wire it into app/main.py, and create a matching pytest test file. Use when the user asks to add a new FastAPI router, endpoint group, or resource (e.g. "add a /users endpoint", "create a router for products", "scaffold an items API").
---

# add-router

Scaffolds a new FastAPI router for a resource and wires it into the application.

## Inputs

The user will name a resource. Derive these from it:

- `resource_singular` — singular form, lower-case (e.g. `item`)
- `resource_plural` — plural form, lower-case (e.g. `items`); also the URL prefix and router filename
- `ModelName` — PascalCase singular (e.g. `Item`)

If the user only gives one form, infer the others. If ambiguous, ask once.

## Steps

1. Create `app/routers/{resource_plural}.py` using the template in `templates/router.py.tmpl`. Replace placeholders (`{{resource_plural}}`, `{{ModelName}}`, `{{resource_singular}}`).
2. Edit `app/main.py`:
   - Add `from app.routers import {resource_plural}` near the top.
   - Add `app.include_router({resource_plural}.router)` after the `app = FastAPI(...)` line. If other routers are already included, group them.
3. Ensure a `tests/` directory exists with an `__init__.py`. Create `tests/test_{resource_plural}.py` from `templates/test_router.py.tmpl`.
4. Run `uv run pytest tests/test_{resource_plural}.py -q` to verify the scaffold works. If pytest fails, fix the scaffold (do not mark the skill done with failing tests).
5. Report what was created in a short bullet list.

## Conventions

- Use Pydantic models for request/response bodies, defined at the top of the router file.
- Use an in-memory `dict[int, ModelName]` store as a placeholder — annotate with a `# TODO: replace with real persistence` comment.
- Return `404` via `HTTPException` for missing items.
- Use modern type hints (`list[ModelName]`, `dict[str, str]`, `ModelName | None`).
- Keep handlers thin; no business logic beyond store access.

## Do not

- Do not add database, auth, or migration code — this is a scaffold.
- Do not create a router if one already exists at the target path — instead, tell the user and stop.
