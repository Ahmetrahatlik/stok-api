"""Sample data for the public demo. Loaded only when DEMO_SEED=1 and the database is empty."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer, MovementType, PaymentType, Product, Sale, SaleItem, StockMovement, User, search_key

PRODUCTS = [
    # name, unit, purchase, sale, stock, min_stock
    ("Çekiç", "adet", "80", "120", "25", "5"),
    ("Tornavida Seti", "adet", "150", "230", "12", "3"),
    ("İnşaat Çivisi 5 cm", "kg", "45", "70", "40", "10"),
    ("Silikon", "adet", "60", "95", "4", "6"),
    ("Matkap Ucu Seti", "adet", "210", "320", "8", "2"),
    ("Su Terazisi", "adet", "95", "150", "2", "3"),
]


DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo1234"


def seed_demo_data(session: Session) -> None:
    from app.auth import create_user

    if session.scalar(select(User.id).where(User.username == DEMO_USERNAME)) is None:
        create_user(session, DEMO_USERNAME, DEMO_PASSWORD)
    if session.scalar(select(Product.id).limit(1)) is not None:
        return
    products = [
        Product(
            name=name,
            name_key=search_key(name),
            unit=unit,
            purchase_price=Decimal(buy),
            sale_price=Decimal(sell),
            stock=Decimal(stock),
            min_stock=Decimal(minimum),
        )
        for name, unit, buy, sell, stock, minimum in PRODUCTS
    ]
    session.add_all(products)
    mehmet = Customer(name="Mehmet Usta", phone="0555 000 00 00", balance=Decimal("0"))
    ayse = Customer(name="Ayşe Hanım", balance=Decimal("0"))
    session.add_all([mehmet, ayse])
    session.flush()

    for product in products:
        session.add(StockMovement(product_id=product.id, type=MovementType.PURCHASE, quantity=product.stock, unit_cost=product.purchase_price))

    hammer, nails = products[0], products[2]
    sale = Sale(customer_id=mehmet.id, payment_type=PaymentType.CREDIT, total=Decimal("0"), cost=Decimal("0"))
    for product, quantity in ((hammer, Decimal("2")), (nails, Decimal("3"))):
        product.stock -= quantity
        sale.items.append(SaleItem(product_id=product.id, quantity=quantity, unit_price=product.sale_price, unit_cost=product.purchase_price))
        session.add(StockMovement(product_id=product.id, type=MovementType.SALE, quantity=-quantity))
        sale.total += product.sale_price * quantity
        sale.cost += product.purchase_price * quantity
    mehmet.balance += sale.total
    session.add(sale)
    session.commit()
