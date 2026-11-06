from decimal import Decimal

from app.db import SessionLocal
from app.demo import seed_demo_data


def test_demo_seed_is_consistent_and_runs_once(client):
    with SessionLocal() as session:
        seed_demo_data(session)
        seed_demo_data(session)

    products = client.get("/products").json()
    assert len(products) == 6
    hammer = next(p for p in products if p["name"] == "Çekiç")
    assert Decimal(hammer["stock"]) == 23

    report = client.get("/reports/profit").json()
    assert Decimal(report["revenue"]) == Decimal("450")
    assert Decimal(report["receivables"]) == Decimal("450")
    assert {p["name"] for p in client.get("/products/low-stock").json()} == {"Silikon", "Su Terazisi"}
    assert client.get("/", follow_redirects=False).headers["location"] == "/docs"
