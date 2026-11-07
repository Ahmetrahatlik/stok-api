import os

# Tests use an in-memory SQLite database unless CI provides PostgreSQL.
os.environ.setdefault("DATABASE_URL", "sqlite://")
# Cheap password hashing keeps the suite fast; production uses the default cost.
os.environ.setdefault("BCRYPT_ROUNDS", "4")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.auth import create_user  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def anon():
    """A client with an empty database and no login."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def client(anon):
    """A client logged in as a test user."""
    with SessionLocal() as session:
        create_user(session, "kasiyer", "gizli-sifre")
    token = anon.post("/auth/token", data={"username": "kasiyer", "password": "gizli-sifre"}).json()["access_token"]
    anon.headers["Authorization"] = f"Bearer {token}"
    return anon


@pytest.fixture()
def hammer(client):
    response = client.post(
        "/products",
        json={"name": "Çekiç", "purchase_price": "80.00", "sale_price": "120.00", "min_stock": "5"},
    )
    return response.json()


@pytest.fixture()
def customer(client):
    return client.post("/customers", json={"name": "Mehmet Usta", "phone": "05550000000"}).json()


def buy(client, product_id, quantity, unit_cost=None):
    body = {"product_id": product_id, "quantity": str(quantity)}
    if unit_cost is not None:
        body["unit_cost"] = str(unit_cost)
    response = client.post("/stock/purchases", json=body)
    assert response.status_code == 201, response.text
    return response.json()
