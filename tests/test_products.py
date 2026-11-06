from decimal import Decimal

from tests.conftest import buy


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_get_product(client, hammer):
    assert Decimal(hammer["stock"]) == 0
    response = client.get(f"/products/{hammer['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Çekiç"


def test_duplicate_name_is_rejected(client, hammer):
    response = client.post("/products", json={"name": "Çekiç", "purchase_price": "1", "sale_price": "2"})
    assert response.status_code == 409


def test_negative_price_is_rejected(client):
    response = client.post("/products", json={"name": "Vida", "purchase_price": "-1", "sale_price": "2"})
    assert response.status_code == 422


def test_search_and_update(client, hammer):
    client.post("/products", json={"name": "Tornavida", "purchase_price": "20", "sale_price": "35"})
    names = [p["name"] for p in client.get("/products", params={"search": "torna"}).json()]
    assert names == ["Tornavida"]

    response = client.patch(f"/products/{hammer['id']}", json={"sale_price": "130.00"})
    assert Decimal(response.json()["sale_price"]) == Decimal("130")


def test_search_handles_turkish_case(client, hammer):
    client.post("/products", json={"name": "İnşaat Çivisi", "purchase_price": "1", "sale_price": "2"})
    assert [p["name"] for p in client.get("/products", params={"search": "çek"}).json()] == ["Çekiç"]
    assert [p["name"] for p in client.get("/products", params={"search": "ÇEKİÇ"}).json()] == ["Çekiç"]
    assert [p["name"] for p in client.get("/products", params={"search": "inşaat"}).json()] == ["İnşaat Çivisi"]
    assert client.get("/products", params={"search": "%"}).json() == []


def test_missing_product_returns_404(client):
    assert client.get("/products/999").status_code == 404


def test_purchase_increases_stock_and_updates_cost(client, hammer):
    buy(client, hammer["id"], 10, unit_cost="85.00")
    product = client.get(f"/products/{hammer['id']}").json()
    assert Decimal(product["stock"]) == 10
    assert Decimal(product["purchase_price"]) == Decimal("85")


def test_low_stock_list(client, hammer):
    assert [p["id"] for p in client.get("/products/low-stock").json()] == [hammer["id"]]
    buy(client, hammer["id"], 20)
    assert client.get("/products/low-stock").json() == []


def test_adjustment_sets_counted_stock(client, hammer):
    buy(client, hammer["id"], 10)
    response = client.post("/stock/adjustments", json={"product_id": hammer["id"], "counted_stock": "7"})
    assert Decimal(response.json()["quantity"]) == -3
    assert Decimal(client.get(f"/products/{hammer['id']}").json()["stock"]) == 7
    types = [m["type"] for m in client.get("/stock/movements", params={"product_id": hammer["id"]}).json()]
    assert types == ["adjustment", "purchase"]
