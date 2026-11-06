from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_session
from app.models import Customer, MovementType, PaymentType, Product, Sale, SaleItem, StockMovement
from app.schemas import ProfitReport, SaleCreate, SaleOut

router = APIRouter(tags=["sales"])


@router.post("/sales", response_model=SaleOut, status_code=status.HTTP_201_CREATED)
def create_sale(data: SaleCreate, session: Session = Depends(get_session)):
    customer = None
    if data.customer_id is not None:
        customer = session.scalars(
            select(Customer).where(Customer.id == data.customer_id).with_for_update()
        ).first()
        if customer is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Customer {data.customer_id} not found")
    if data.payment_type == PaymentType.CREDIT and customer is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Credit sales need a customer")

    # The same product may appear on several lines; sell the total once.
    wanted: dict[int, Decimal] = defaultdict(Decimal)
    for item in data.items:
        wanted[item.product_id] += item.quantity

    # Lock rows in id order so two concurrent sales cannot deadlock each other.
    products = {
        p.id: p
        for p in session.scalars(
            select(Product).where(Product.id.in_(wanted)).order_by(Product.id).with_for_update()
        )
    }
    missing = sorted(set(wanted) - set(products))
    if missing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Products not found: {missing}")
    short = [
        f"{products[pid].name}: {products[pid].stock} in stock, {qty} requested"
        for pid, qty in wanted.items()
        if products[pid].stock < qty
    ]
    if short:
        raise HTTPException(status.HTTP_409_CONFLICT, {"message": "Insufficient stock", "items": short})

    sale = Sale(customer_id=data.customer_id, payment_type=data.payment_type, total=0, cost=0)
    total = cost = Decimal("0")
    for pid, qty in wanted.items():
        product = products[pid]
        product.stock -= qty
        sale.items.append(
            SaleItem(product_id=pid, quantity=qty, unit_price=product.sale_price, unit_cost=product.purchase_price)
        )
        session.add(StockMovement(product_id=pid, type=MovementType.SALE, quantity=-qty))
        total += product.sale_price * qty
        cost += product.purchase_price * qty
    sale.total = total.quantize(Decimal("0.01"))
    sale.cost = cost.quantize(Decimal("0.01"))
    if data.payment_type == PaymentType.CREDIT:
        customer.balance += sale.total

    session.add(sale)
    session.commit()
    return sale


@router.get("/sales/{sale_id}", response_model=SaleOut)
def get_sale(sale_id: int, session: Session = Depends(get_session)):
    sale = session.scalars(select(Sale).where(Sale.id == sale_id).options(selectinload(Sale.items))).first()
    if sale is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Sale {sale_id} not found")
    return sale


@router.get("/reports/profit", response_model=ProfitReport)
def profit_report(
    start: datetime | None = None, end: datetime | None = None, session: Session = Depends(get_session)
):
    query = select(func.count(Sale.id), func.coalesce(func.sum(Sale.total), 0), func.coalesce(func.sum(Sale.cost), 0))
    if start is not None:
        query = query.where(Sale.created_at >= start)
    if end is not None:
        query = query.where(Sale.created_at < end)
    count, revenue, cost = session.execute(query).one()
    receivables = session.scalar(select(func.coalesce(func.sum(Customer.balance), 0)))
    revenue, cost = Decimal(revenue), Decimal(cost)
    return ProfitReport(
        sale_count=count,
        revenue=revenue,
        cost=cost,
        gross_profit=revenue - cost,
        receivables=Decimal(receivables),
    )
