---
name: log-til
description: Log a "Today I Learned" entry directly into the project's Supabase database. Use when the user says things like "log: <text>", "TIL: <text>", "today I learned <text>", "journal this: <text>", or otherwise asks to record a learning into the TIL journal. Auto-tags the entry via the configured LLM client and reports what was saved. Requires SUPABASE_URL and SUPABASE_KEY to be set (typically via .env).
---

# log-til

Records a TIL entry by invoking the project's own create-entry logic, which writes to Supabase via the configured HTTP client. No server needs to be running, but `SUPABASE_URL` and `SUPABASE_KEY` must be present in the environment (or `.env`).

## Inputs

- `text` (required) — the learning, in the user's own words. Strip leading filler ("log:", "TIL:", "today I learned ") before saving.
- `source` (optional) — a URL, book title, repo, or person, if mentioned.
- `tags` (optional) — only if the user explicitly listed them. Otherwise let the LLM auto-tag.

## Steps

1. From `<text>`, strip leading prefixes: `^(log|til|today i learned|journal(?: this)?)\s*[:\-]?\s*` (case-insensitive).
2. Run the script via `uv run python .claude/skills/log-til/scripts/log.py <args>`. Use the JSON-stdin form for safety:

   ```bash
   echo '{"text": "...", "source": "...", "tags": ["..."]}' | \
       uv run python .claude/skills/log-til/scripts/log.py
   ```

   Omit `source` and `tags` if not supplied.

3. The script prints the created entry as JSON. Report back to the user:
   - Entry id
   - Tags (auto-generated or explicit)
   - Confirmation of what was saved

## Conventions

- The script reads `SUPABASE_URL` / `SUPABASE_KEY` from the environment or `.env` and writes via the same `app.routers.entries.create_entry` function the HTTP API uses.
- Do **not** start the FastAPI server to log an entry — this skill bypasses HTTP and uses the create function directly.
- Never include the prefix words (TIL/log/etc.) in the saved `text`.

## Do not

- Do not invent a `source` if the user did not mention one.
- Do not strip valuable context from the learning text — only the prefix.
