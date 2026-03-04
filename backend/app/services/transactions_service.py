from typing import Any

import psycopg

from app.repositories.transactions_repository import create_transaction
from app.core.constants.transactions import (
  DEFAULT_INCOME_CATEGORY,
  DEFAULT_INCOME_PAYMENT_METHOD,
  TX_STATUS_SUBMITTED,
  TX_TYPE_EXPENSE,
  TX_TYPE_INCOME,
)
from app.schemas.transactions import ExpenseCreate, IncomeCreate


def create_income_transaction(conn: psycopg.Connection, user_id: str, payload: IncomeCreate) -> dict[str, Any]:
  transaction_payload = {
    "type": TX_TYPE_INCOME,
    "amount": payload.amount,
    "category": DEFAULT_INCOME_CATEGORY,
    "merchant": None,
    "source": payload.source,
    "description": payload.description,
    "payment_method": DEFAULT_INCOME_PAYMENT_METHOD,
    "status": TX_STATUS_SUBMITTED,
    "entry_date": payload.entry_date,
  }
  return create_transaction(conn, user_id, transaction_payload)


def create_expense_transaction(conn: psycopg.Connection, user_id: str, payload: ExpenseCreate) -> dict[str, Any]:
  transaction_payload = {
    "type": TX_TYPE_EXPENSE,
    "amount": payload.amount,
    "category": payload.category,
    "merchant": payload.merchant,
    "source": None,
    "description": payload.description,
    "payment_method": payload.payment_method,
    "status": payload.status,
    "entry_date": payload.entry_date,
  }
  return create_transaction(conn, user_id, transaction_payload)
