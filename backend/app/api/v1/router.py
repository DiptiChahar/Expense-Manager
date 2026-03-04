from fastapi import APIRouter

from app.auth import auth_router
from app.api.v1.endpoints import analytics, bills, budgets, expenses, goals, health, income, transactions

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth_router.router)
api_router.include_router(transactions.router)
api_router.include_router(income.router)
api_router.include_router(expenses.router)
api_router.include_router(budgets.router)
api_router.include_router(goals.router)
api_router.include_router(bills.router)
api_router.include_router(analytics.router)
