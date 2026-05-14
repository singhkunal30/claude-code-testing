"""Environment-driven configuration.

Loads .env on import (no-op if missing) so the dev workflow is just:
    1) cp .env.example .env  2) fill in values  3) uv run uvicorn ...
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv(override=False)


class Settings(BaseModel):
    supabase_url: str
    supabase_key: str
    supabase_anon_key: str = ""
    supabase_schema: str = "public"


@lru_cache(maxsize=1)
def settings() -> Settings:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_KEY", "")
    anon = os.environ.get("SUPABASE_ANON_KEY", "")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set. "
            "Copy .env.example to .env and fill in values from your Supabase "
            "project's Settings → API page."
        )
    return Settings(
        supabase_url=url,
        supabase_key=key,
        supabase_anon_key=anon,
        supabase_schema=os.environ.get("SUPABASE_SCHEMA", "public"),
    )
