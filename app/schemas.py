from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import MovementType, PaymentType

PositiveMoney = Field(gt=0, max_digits=12, decimal_places=2)
NonNegativeMoney = Field(ge=0, max_digits=12, decimal_places=2)
PositiveQuantity = Field(gt=0, max_digits=12, decimal_places=3)


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    unit: str = Field(default="adet", max_length=20)
    purchase_price: Decimal = NonNegativeMoney
    sale_price: Decimal = NonNegativeMoney
    min_stock: Decimal = Field(default=Decimal("0"), ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    unit: str | None = Field(default=None, max_length=20)
    purchase_price: Decimal | None = Field(default=None, ge=0)
    sale_price: Decimal | None = Field(default=None, ge=0)
    min_stock: Decimal | None = Field(default=None, ge=0)


class ProductOut(ORM):
    id: int
    name: str
    unit: str
    purchase_price: Decimal
    sale_price: Decimal
    stock: Decimal
    min_stock: Decimal


class PurchaseIn(BaseModel):
    product_id: int
    quantity: Decimal = PositiveQuantity
    unit_cost: Decimal | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=200)


class AdjustmentIn(BaseModel):
    product_id: int
    counted_stock: Decimal = Field(ge=0)
    note: str | None = Field(default=None, max_length=200)


class MovementOut(ORM):
    id: int
    product_id: int
    type: MovementType
    quantity: Decimal
    unit_cost: Decimal | None
    note: str | None
    created_at: datetime


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=30)


class CustomerOut(ORM):
    id: int
    name: str
    phone: str | None
    balance: Decimal


class PaymentIn(BaseModel):
    amount: Decimal = PositiveMoney


class SaleItemIn(BaseModel):
    product_id: int
    quantity: Decimal = PositiveQuantity


class SaleCreate(BaseModel):
    items: list[SaleItemIn] = Field(min_length=1)
    payment_type: PaymentType = PaymentType.CASH
    customer_id: int | None = None


class SaleItemOut(ORM):
    product_id: int
    quantity: Decimal
    unit_price: Decimal


class SaleOut(ORM):
    id: int
    customer_id: int | None
    payment_type: PaymentType
    total: Decimal
    created_at: datetime
    items: list[SaleItemOut]


class ProfitReport(BaseModel):
    sale_count: int
    revenue: Decimal
    cost: Decimal
    gross_profit: Decimal
    receivables: Decimal
