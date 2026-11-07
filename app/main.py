import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app import auth
from app.db import SessionLocal
from app.demo import seed_demo_data
from app.models import User
from app.routers import customers, products, sales, stock


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Tables come from Alembic migrations (`alembic upgrade head`), not from create_all.
    with SessionLocal() as session:
        admin, password = os.getenv("ADMIN_USERNAME"), os.getenv("ADMIN_PASSWORD")
        if admin and password and session.scalar(select(User.id).limit(1)) is None:
            auth.create_user(session, admin, password)
        if os.getenv("DEMO_SEED") == "1":
            seed_demo_data(session)
    yield


app = FastAPI(
    title="Stok API",
    description="Stock, sales and customer credit (veresiye) API for a small hardware shop. "
    "Reading is public; changing data needs a JWT from /auth/token.",
    version="1.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(stock.router)
app.include_router(customers.router)
app.include_router(sales.router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
