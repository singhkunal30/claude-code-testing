"""Thin Supabase / PostgREST access layer.

Two implementations behind one interface:
- `_HttpClient`: real httpx-backed client that talks to Supabase.
- `_InMemory`: an in-memory fake that mimics enough PostgREST behaviour
  for tests. Selected via `set_client(...)`.

The router code is the only consumer; both implementations share the
same `SupabaseClient` Protocol.
"""
from __future__ import annotations

import itertools
import json
import re
from typing import Any, Iterable, Protocol

import httpx

from app.config import settings


Row = dict[str, Any]
Filters = dict[str, tuple[str, Any]]  # column -> (op, value), op in {eq, in, gte, lte, lt, gt}


class SupabaseClient(Protocol):
    def select(
        self,
        table: str,
        *,
        filters: Filters | None = None,
        order: str | None = None,
        limit: int | None = None,
        columns: str = "*",
    ) -> list[Row]: ...

    def insert(self, table: str, rows: Row | list[Row]) -> list[Row]: ...

    def upsert(
        self,
        table: str,
        rows: Row | list[Row],
        *,
        on_conflict: str,
    ) -> list[Row]: ...

    def delete(self, table: str, *, filters: Filters) -> list[Row]: ...


# ---------------------------------------------------------------------------
# Real httpx-backed client
# ---------------------------------------------------------------------------
def _params_from_filters(filters: Filters | None) -> list[tuple[str, str]]:
    if not filters:
        return []
    out: list[tuple[str, str]] = []
    for col, (op, value) in filters.items():
        if op == "in":
            joined = ",".join(str(v) for v in value)
            out.append((col, f"in.({joined})"))
        else:
            out.append((col, f"{op}.{value}"))
    return out


class _HttpClient:
    def __init__(self, base_url: str, key: str, schema: str = "public") -> None:
        self._http = httpx.Client(
            base_url=f"{base_url}/rest/v1",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Profile": schema,
                "Accept-Profile": schema,
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )

    def _request(self, method: str, table: str, **kwargs: Any) -> list[Row]:
        r = self._http.request(method, f"/{table}", **kwargs)
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase {method} /{table} failed: {r.status_code} {r.text}")
        return r.json() if r.text else []

    def select(
        self,
        table: str,
        *,
        filters: Filters | None = None,
        order: str | None = None,
        limit: int | None = None,
        columns: str = "*",
    ) -> list[Row]:
        params: list[tuple[str, str]] = [("select", columns)]
        params.extend(_params_from_filters(filters))
        if order:
            params.append(("order", order))
        if limit is not None:
            params.append(("limit", str(limit)))
        return self._request("GET", table, params=params)

    def insert(self, table: str, rows: Row | list[Row]) -> list[Row]:
        return self._request(
            "POST",
            table,
            content=json.dumps(rows if isinstance(rows, list) else [rows]),
            headers={"Prefer": "return=representation"},
        )

    def upsert(self, table: str, rows: Row | list[Row], *, on_conflict: str) -> list[Row]:
        return self._request(
            "POST",
            table,
            params=[("on_conflict", on_conflict)],
            content=json.dumps(rows if isinstance(rows, list) else [rows]),
            headers={"Prefer": "return=representation,resolution=merge-duplicates"},
        )

    def delete(self, table: str, *, filters: Filters) -> list[Row]:
        return self._request(
            "DELETE",
            table,
            params=_params_from_filters(filters),
            headers={"Prefer": "return=representation"},
        )


# ---------------------------------------------------------------------------
# In-memory fake for tests
# ---------------------------------------------------------------------------
_ORDER_RE = re.compile(r"^([a-zA-Z_][\w]*)(?:\.(asc|desc))?$")


def _passes_filter(row: Row, filters: Filters) -> bool:
    for col, (op, value) in filters.items():
        cur = row.get(col)
        if op == "eq" and cur != value:
            return False
        if op == "in" and cur not in value:
            return False
        if op == "gte" and not (cur is not None and cur >= value):
            return False
        if op == "lte" and not (cur is not None and cur <= value):
            return False
        if op == "gt" and not (cur is not None and cur > value):
            return False
        if op == "lt" and not (cur is not None and cur < value):
            return False
    return True


class _InMemory:
    def __init__(self) -> None:
        self._tables: dict[str, list[Row]] = {}
        self._seq = itertools.count(1)
        # Tables with composite primary keys (no auto id).
        self._composite_pk: dict[str, tuple[str, ...]] = {
            "entry_tags": ("entry_id", "tag_id"),
            "bookmark_tags": ("bookmark_id", "tag_id"),
        }

    def _t(self, table: str) -> list[Row]:
        return self._tables.setdefault(table, [])

    def _insert_one(self, table: str, row: Row) -> Row:
        rows = self._t(table)
        if table not in self._composite_pk and "id" not in row:
            row = {"id": next(self._seq), **row}
        if "created_at" not in row and table in ("entries", "bookmarks", "digests"):
            from datetime import datetime, timezone

            row = {**row, "created_at": datetime.now(timezone.utc).isoformat()}
        rows.append(row)
        return row

    def select(
        self,
        table: str,
        *,
        filters: Filters | None = None,
        order: str | None = None,
        limit: int | None = None,
        columns: str = "*",
    ) -> list[Row]:
        rows = list(self._t(table))
        if filters:
            rows = [r for r in rows if _passes_filter(r, filters)]
        if order:
            m = _ORDER_RE.match(order)
            if m:
                col, direction = m.group(1), m.group(2) or "asc"
                rows.sort(key=lambda r: (r.get(col) is None, r.get(col)), reverse=(direction == "desc"))
        if limit is not None:
            rows = rows[:limit]
        return [dict(r) for r in rows]

    def insert(self, table: str, rows: Row | list[Row]) -> list[Row]:
        items: Iterable[Row] = rows if isinstance(rows, list) else [rows]
        return [self._insert_one(table, r) for r in items]

    def upsert(self, table: str, rows: Row | list[Row], *, on_conflict: str) -> list[Row]:
        items: list[Row] = list(rows) if isinstance(rows, list) else [rows]
        result: list[Row] = []
        keys = [k.strip() for k in on_conflict.split(",")]
        existing = self._t(table)
        for r in items:
            match = next(
                (e for e in existing if all(e.get(k) == r.get(k) for k in keys)),
                None,
            )
            if match is None:
                result.append(self._insert_one(table, r))
            else:
                match.update(r)
                result.append(match)
        return result

    def delete(self, table: str, *, filters: Filters) -> list[Row]:
        rows = self._t(table)
        kept: list[Row] = []
        removed: list[Row] = []
        for r in rows:
            if _passes_filter(r, filters):
                removed.append(r)
            else:
                kept.append(r)
        self._tables[table] = kept

        # Emulate FK ON DELETE CASCADE for our schema.
        if table == "entries":
            removed_ids = {r["id"] for r in removed}
            self._tables["entry_tags"] = [
                r for r in self._t("entry_tags") if r["entry_id"] not in removed_ids
            ]
        if table == "bookmarks":
            removed_ids = {r["id"] for r in removed}
            self._tables["bookmark_tags"] = [
                r for r in self._t("bookmark_tags") if r["bookmark_id"] not in removed_ids
            ]
        return removed


# ---------------------------------------------------------------------------
# Singleton + test seam
# ---------------------------------------------------------------------------
_client: SupabaseClient | None = None


def set_client(c: SupabaseClient) -> None:
    global _client
    _client = c


def client() -> SupabaseClient:
    global _client
    if _client is None:
        s = settings()
        _client = _HttpClient(s.supabase_url, s.supabase_key, s.supabase_schema)
    return _client


def reset_for_tests() -> _InMemory:
    """Replace the active client with a fresh in-memory fake. Returns it."""
    fake = _InMemory()
    set_client(fake)
    return fake
