from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.supabase import reset_for_tests


@pytest.fixture()
def client() -> Iterator[TestClient]:
    reset_for_tests()  # fresh in-memory Supabase per test
    from app.main import app

    with TestClient(app) as c:
        yield c
