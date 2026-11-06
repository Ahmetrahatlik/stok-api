from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Product
from app.schemas import ProductCreate, ProductOut, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


def get_product_or_404(session: Session, product_id: int) -> Product:
    product = session.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Product {product_id} not found")
    return product


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, session: Session = Depends(get_session)):
    product = Product(**data.model_dump())
    session.add(product)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "A product with this name already exists")
    return product


@router.get("", response_model=list[ProductOut])
def list_products(search: str | None = None, session: Session = Depends(get_session)):
    query = select(Product).order_by(Product.name)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    return session.scalars(query).all()


@router.get("/low-stock", response_model=list[ProductOut])
def low_stock(session: Session = Depends(get_session)):
    query = select(Product).where(Product.stock <= Product.min_stock).order_by(Product.name)
    return session.scalars(query).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, session: Session = Depends(get_session)):
    return get_product_or_404(session, product_id)


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductUpdate, session: Session = Depends(get_session)):
    product = get_product_or_404(session, product_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "A product with this name already exists")
    return product
