"""Initial schema: users, products, stock movements, customers, sales, payments.

Revision ID: 0001
Revises:
Create Date: 2026-11-07
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

MONEY = sa.Numeric(12, 2)
QUANTITY = sa.Numeric(12, 3)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("name_key", sa.String(120), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("purchase_price", MONEY, nullable=False),
        sa.Column("sale_price", MONEY, nullable=False),
        sa.Column("stock", QUANTITY, nullable=False),
        sa.Column("min_stock", QUANTITY, nullable=False),
        sa.CheckConstraint("stock >= 0", name="stock_not_negative"),
    )
    op.create_index("ix_products_name_key", "products", ["name_key"])
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("type", sa.Enum("PURCHASE", "SALE", "ADJUSTMENT", name="movementtype", native_enum=False), nullable=False),
        sa.Column("quantity", QUANTITY, nullable=False),
        sa.Column("unit_cost", MONEY, nullable=True),
        sa.Column("note", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("balance", MONEY, nullable=False),
    )
    op.create_table(
        "sales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("payment_type", sa.Enum("CASH", "CREDIT", name="paymenttype", native_enum=False), nullable=False),
        sa.Column("total", MONEY, nullable=False),
        sa.Column("cost", MONEY, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "sale_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sale_id", sa.Integer(), sa.ForeignKey("sales.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", QUANTITY, nullable=False),
        sa.Column("unit_price", MONEY, nullable=False),
        sa.Column("unit_cost", MONEY, nullable=False),
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in ("payments", "sale_items", "sales", "customers", "stock_movements", "products", "users"):
        op.drop_table(table)
