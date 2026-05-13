from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("TIL_DB_PATH", str(db_path))

    # Re-import inside the fixture so app.db picks up the env var.
    from app.main import app

    with TestClient(app) as c:
        yield c
