"""
Web3 Service API Routes
"""
from fastapi import APIRouter

from app.api.endpoints import wallets, transactions, defi, gas

router = APIRouter()

router.include_router(wallets.router, prefix="/wallets", tags=["Wallets"])
router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
router.include_router(defi.router, prefix="/defi", tags=["DeFi"])
router.include_router(gas.router, prefix="/gas", tags=["Gas"])

