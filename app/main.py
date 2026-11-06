import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.db import Base, SessionLocal, engine
from app.demo import seed_demo_data
from app.routers import customers, products, sales, stock


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    if os.getenv("DEMO_SEED") == "1":
        with SessionLocal() as session:
            seed_demo_data(session)
    yield


app = FastAPI(
    title="Stok API",
    description="Stock, sales and customer credit (veresiye) API for a small hardware shop.",
    version="1.0.0",
    lifespan=lifespan,
)
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
