from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import MovementType, Product, StockMovement
from app.schemas import AdjustmentIn, MovementOut, PurchaseIn

router = APIRouter(prefix="/stock", tags=["stock"])


def lock_product(session: Session, product_id: int) -> Product:
    # FOR UPDATE keeps two requests from changing the same stock at once (no-op on SQLite).
    product = session.scalars(select(Product).where(Product.id == product_id).with_for_update()).first()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Product {product_id} not found")
    return product


@router.post("/purchases", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def record_purchase(data: PurchaseIn, session: Session = Depends(get_session)):
    product = lock_product(session, data.product_id)
    product.stock += data.quantity
    if data.unit_cost is not None:
        product.purchase_price = data.unit_cost
    movement = StockMovement(
        product_id=product.id,
        type=MovementType.PURCHASE,
        quantity=data.quantity,
        unit_cost=data.unit_cost if data.unit_cost is not None else product.purchase_price,
        note=data.note,
    )
    session.add(movement)
    session.commit()
    return movement


@router.post("/adjustments", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def record_adjustment(data: AdjustmentIn, session: Session = Depends(get_session)):
    """Sets stock to a physically counted value and records the difference."""
    product = lock_product(session, data.product_id)
    difference = data.counted_stock - product.stock
    product.stock = data.counted_stock
    movement = StockMovement(
        product_id=product.id, type=MovementType.ADJUSTMENT, quantity=difference, note=data.note
    )
    session.add(movement)
    session.commit()
    return movement


@router.get("/movements", response_model=list[MovementOut])
def list_movements(product_id: int | None = None, session: Session = Depends(get_session)):
    query = select(StockMovement).order_by(StockMovement.id.desc())
    if product_id is not None:
        query = query.where(StockMovement.product_id == product_id)
    return session.scalars(query).all()
