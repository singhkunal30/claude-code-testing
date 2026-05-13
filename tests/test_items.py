from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_items_empty() -> None:
    r = client.get("/items")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_and_get_item() -> None:
    r = client.post("/items", json={"name": "example"})
    assert r.status_code == 201
    created = r.json()
    assert created["name"] == "example"
    assert "id" in created

    r = client.get(f"/items/{created['id']}")
    assert r.status_code == 200
    assert r.json() == created


def test_get_missing_item_returns_404() -> None:
    r = client.get("/items/999999")
    assert r.status_code == 404
