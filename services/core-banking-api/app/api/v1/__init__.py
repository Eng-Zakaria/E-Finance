"""
API Version 1
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, accounts, transactions, cards

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
router.include_router(cards.router, prefix="/cards", tags=["Cards"])

