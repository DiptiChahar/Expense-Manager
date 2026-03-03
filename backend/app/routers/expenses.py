from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.transactions import ExpenseCreate
from app.utils.db import fetch_all
from app.utils.transactions import create_transaction_record

router = APIRouter(tags=["expenses"])


@router.get("/expenses")
def list_expenses() -> list[dict[str, Any]]:
  return fetch_all(
    """
    SELECT id, type, amount, category, merchant, source, description, payment_method, status, entry_date, created_at
    FROM transactions
    WHERE type = 'expense'
    ORDER BY entry_date DESC, created_at DESC
    """
  )


@router.post("/expenses", status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate) -> dict[str, Any]:
  transaction_payload = {
    "type": "expense",
    "amount": payload.amount,
    "category": payload.category,
    "merchant": payload.merchant,
    "source": None,
    "description": payload.description,
    "payment_method": payload.payment_method,
    "status": payload.status,
    "entry_date": payload.entry_date,
  }

  try:
    return create_transaction_record(transaction_payload)
  except RuntimeError as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc
