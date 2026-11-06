from decimal import Decimal

from tests.conftest import buy


def stock_of(client, product_id):
    return Decimal(client.get(f"/products/{product_id}").json()["stock"])


def test_cash_sale_reduces_stock(client, hammer):
    buy(client, hammer["id"], 10)
    response = client.post("/sales", json={"items": [{"product_id": hammer["id"], "quantity": "3"}]})
    assert response.status_code == 201
    assert Decimal(response.json()["total"]) == Decimal("360")
    assert stock_of(client, hammer["id"]) == 7


def test_insufficient_stock_rolls_back_whole_sale(client, hammer):
    nail = client.post("/products", json={"name": "Çivi", "purchase_price": "1", "sale_price": "2"}).json()
    buy(client, hammer["id"], 5)
    buy(client, nail["id"], 1)
    response = client.post(
        "/sales",
        json={"items": [{"product_id": hammer["id"], "quantity": "2"}, {"product_id": nail["id"], "quantity": "3"}]},
    )
    assert response.status_code == 409
    assert stock_of(client, hammer["id"]) == 5
    assert stock_of(client, nail["id"]) == 1


def test_same_product_on_two_lines_is_checked_together(client, hammer):
    buy(client, hammer["id"], 3)
    items = [{"product_id": hammer["id"], "quantity": "2"}, {"product_id": hammer["id"], "quantity": "2"}]
    assert client.post("/sales", json={"items": items}).status_code == 409
    assert stock_of(client, hammer["id"]) == 3


def test_credit_sale_needs_customer(client, hammer):
    buy(client, hammer["id"], 5)
    response = client.post(
        "/sales", json={"items": [{"product_id": hammer["id"], "quantity": "1"}], "payment_type": "credit"}
    )
    assert response.status_code == 422


def test_credit_sale_and_payment_update_balance(client, hammer, customer):
    buy(client, hammer["id"], 5)
    client.post(
        "/sales",
        json={
            "items": [{"product_id": hammer["id"], "quantity": "2"}],
            "payment_type": "credit",
            "customer_id": customer["id"],
        },
    )
    assert Decimal(client.get(f"/customers/{customer['id']}").json()["balance"]) == 240
    debtors = client.get("/customers", params={"with_debt": True}).json()
    assert [c["id"] for c in debtors] == [customer["id"]]

    paid = client.post(f"/customers/{customer['id']}/payments", json={"amount": "100"})
    assert Decimal(paid.json()["balance"]) == 140

    too_much = client.post(f"/customers/{customer['id']}/payments", json={"amount": "500"})
    assert too_much.status_code == 422


def test_profit_report(client, hammer, customer):
    buy(client, hammer["id"], 10, unit_cost="80.00")
    client.post("/sales", json={"items": [{"product_id": hammer["id"], "quantity": "2"}]})
    client.post(
        "/sales",
        json={
            "items": [{"product_id": hammer["id"], "quantity": "1"}],
            "payment_type": "credit",
            "customer_id": customer["id"],
        },
    )
    report = client.get("/reports/profit").json()
    assert report["sale_count"] == 2
    assert Decimal(report["revenue"]) == 360
    assert Decimal(report["cost"]) == 240
    assert Decimal(report["gross_profit"]) == 120
    assert Decimal(report["receivables"]) == 120


def test_sale_keeps_price_at_time_of_sale(client, hammer):
    buy(client, hammer["id"], 5)
    sale = client.post("/sales", json={"items": [{"product_id": hammer["id"], "quantity": "1"}]}).json()
    client.patch(f"/products/{hammer['id']}", json={"sale_price": "999"})
    stored = client.get(f"/sales/{sale['id']}").json()
    assert Decimal(stored["items"][0]["unit_price"]) == 120
