from datetime import datetime, timedelta, timezone

import jwt

from app.auth import JWT_ALGORITHM, JWT_SECRET


def test_reading_is_public(anon):
    assert anon.get("/products").status_code == 200
    assert anon.get("/reports/profit").status_code == 200


def test_writing_needs_login(anon):
    responses = [
        anon.post("/products", json={"name": "Vida", "purchase_price": "1", "sale_price": "2"}),
        anon.post("/stock/purchases", json={"product_id": 1, "quantity": "1"}),
        anon.post("/customers", json={"name": "Ali"}),
        anon.post("/sales", json={"items": [{"product_id": 1, "quantity": "1"}]}),
    ]
    assert [r.status_code for r in responses] == [401, 401, 401, 401]


def test_login_and_me(client):
    assert client.get("/auth/me").json()["username"] == "kasiyer"


def test_wrong_password_is_rejected(client):
    response = client.post("/auth/token", data={"username": "kasiyer", "password": "yanlis"})
    assert response.status_code == 401
    assert client.post("/auth/token", data={"username": "yok", "password": "x"}).status_code == 401


def test_expired_and_forged_tokens_are_rejected(anon, client):
    expired = jwt.encode({"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    forged = jwt.encode({"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, "baska-anahtar", algorithm=JWT_ALGORITHM)
    for token in (expired, forged, "bozuk-token"):
        response = anon.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


def test_passwords_are_not_stored_in_plain_text(client):
    from app.db import SessionLocal
    from app.models import User

    with SessionLocal() as session:
        stored = session.query(User).one().password_hash
    assert "gizli-sifre" not in stored and stored.startswith("$2")
