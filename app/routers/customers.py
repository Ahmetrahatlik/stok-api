from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_session
from app.models import Customer, Payment
from app.schemas import CustomerCreate, CustomerOut, PaymentIn

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(current_user)])
def create_customer(data: CustomerCreate, session: Session = Depends(get_session)):
    customer = Customer(**data.model_dump())
    session.add(customer)
    session.commit()
    return customer


@router.get("", response_model=list[CustomerOut])
def list_customers(with_debt: bool = False, session: Session = Depends(get_session)):
    query = select(Customer).order_by(Customer.name)
    if with_debt:
        query = query.where(Customer.balance > 0)
    return session.scalars(query).all()


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, session: Session = Depends(get_session)):
    customer = session.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Customer {customer_id} not found")
    return customer


@router.post("/{customer_id}/payments", response_model=CustomerOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(current_user)])
def record_payment(customer_id: int, data: PaymentIn, session: Session = Depends(get_session)):
    customer = session.scalars(select(Customer).where(Customer.id == customer_id).with_for_update()).first()
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Customer {customer_id} not found")
    if data.amount > customer.balance:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Payment {data.amount} is more than the customer's debt {customer.balance}",
        )
    customer.balance -= data.amount
    session.add(Payment(customer_id=customer.id, amount=data.amount))
    session.commit()
    return customer
