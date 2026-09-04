import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.core.config import get_settings
from app.api.routes import (
    auth, merchants, products, payment_codes,
    charges, payments, webhooks,
    transactions, withdrawals,
    billing, admin, health,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    docs_url="/docs" if settings.environment != "prod" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(health.router,        prefix="/health",       tags=["Health"])
app.include_router(auth.router,          prefix="/auth",         tags=["Auth"])
app.include_router(merchants.router,     prefix="/merchants",    tags=["Merchants"])
app.include_router(products.router,      prefix="",              tags=["Products"])
app.include_router(payment_codes.router, prefix="",              tags=["Payment Codes"])
app.include_router(charges.router,       prefix="",              tags=["Charges"])
app.include_router(payments.router,      prefix="/payments",     tags=["Payments"])
app.include_router(webhooks.router,      prefix="/webhooks",     tags=["Webhooks"])
app.include_router(transactions.router,  prefix="",              tags=["Transactions"])
app.include_router(withdrawals.router,   prefix="",              tags=["Withdrawals"])
app.include_router(billing.router,       prefix="",              tags=["Billing"])
app.include_router(admin.router,         prefix="/admin",        tags=["Admin"])

# ── Lambda handler ────────────────────────────────────────────────────────────
handler = Mangum(app, lifespan="off")
