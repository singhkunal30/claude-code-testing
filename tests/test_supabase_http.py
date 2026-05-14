"""Verify the real httpx-based Supabase client builds correct requests.

Uses httpx.MockTransport so we test the wire-format (URL, headers, body,
PostgREST filter syntax) without a network call.
"""
from __future__ import annotations

import json

import httpx

from app.supabase import _HttpClient


def _make_client(handler) -> _HttpClient:
    c = _HttpClient.__new__(_HttpClient)
    c._http = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://example.supabase.co/rest/v1",
        headers={
            "apikey": "test-key",
            "Authorization": "Bearer test-key",
            "Content-Profile": "public",
            "Accept-Profile": "public",
            "Content-Type": "application/json",
        },
    )
    return c


def test_select_builds_postgrest_url() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["headers"] = dict(request.headers)
        return httpx.Response(200, json=[{"id": 1, "name": "python"}])

    c = _make_client(handler)
    rows = c.select(
        "tags",
        filters={"name": ("eq", "python")},
        order="name.asc",
        limit=5,
    )

    assert rows == [{"id": 1, "name": "python"}]
    assert "select=%2A" in seen["url"] or "select=*" in seen["url"]
    assert "name=eq.python" in seen["url"]
    assert "order=name.asc" in seen["url"]
    assert "limit=5" in seen["url"]
    assert seen["headers"]["apikey"] == "test-key"
    assert seen["headers"]["authorization"] == "Bearer test-key"


def test_select_in_filter() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json=[])

    c = _make_client(handler)
    c.select("entries", filters={"id": ("in", [1, 2, 3])})

    assert "id=in.%281%2C2%2C3%29" in seen["url"] or "id=in.(1,2,3)" in seen["url"]


def test_insert_sends_array_and_return_representation() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["headers"] = dict(request.headers)
        seen["body"] = json.loads(request.content)
        return httpx.Response(201, json=[{"id": 1, "text": "hi"}])

    c = _make_client(handler)
    rows = c.insert("entries", {"text": "hi"})

    assert rows == [{"id": 1, "text": "hi"}]
    assert seen["method"] == "POST"
    assert seen["body"] == [{"text": "hi"}]
    assert seen["headers"]["prefer"] == "return=representation"


def test_upsert_uses_merge_duplicates() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["headers"] = dict(request.headers)
        return httpx.Response(200, json=[{"id": 1, "name": "python"}])

    c = _make_client(handler)
    c.upsert("tags", [{"name": "python"}], on_conflict="name")

    assert "on_conflict=name" in seen["url"]
    assert "merge-duplicates" in seen["headers"]["prefer"]


def test_delete_sends_filters_and_returns_rows() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        return httpx.Response(200, json=[{"id": 7}])

    c = _make_client(handler)
    rows = c.delete("entries", filters={"id": ("eq", 7)})

    assert seen["method"] == "DELETE"
    assert "id=eq.7" in seen["url"]
    assert rows == [{"id": 7}]


def test_update_sends_patch_with_filters() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["headers"] = dict(request.headers)
        return httpx.Response(200, json=[{"id": 7, "share_token": "abc"}])

    c = _make_client(handler)
    rows = c.update("entries", {"share_token": "abc"}, filters={"id": ("eq", 7)})

    assert seen["method"] == "PATCH"
    assert "id=eq.7" in seen["url"]
    assert seen["body"] == {"share_token": "abc"}
    assert seen["headers"]["prefer"] == "return=representation"
    assert rows == [{"id": 7, "share_token": "abc"}]


def test_4xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized")

    c = _make_client(handler)
    try:
        c.select("entries")
    except RuntimeError as e:
        assert "401" in str(e)
    else:
        raise AssertionError("expected RuntimeError on 401")
