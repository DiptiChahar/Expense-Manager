from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.transactions import IncomeCreate
from app.utils.db import fetch_all
from app.utils.transactions import create_transaction_record

router = APIRouter(tags=["income"])


@router.get("/income")
def list_income() -> list[dict[str, Any]]:
  return fetch_all(
    """
    SELECT id, type, amount, category, merchant, source, description, payment_method, status, entry_date, created_at
    FROM transactions
    WHERE type = 'income'
    ORDER BY entry_date DESC, created_at DESC
    """
  )


@router.post("/income", status_code=status.HTTP_201_CREATED)
def create_income(payload: IncomeCreate) -> dict[str, Any]:
  transaction_payload = {
    "type": "income",
    "amount": payload.amount,
    "category": "Income",
    "merchant": None,
    "source": payload.source,
    "description": payload.description,
    "payment_method": "Bank Transfer",
    "status": "submitted",
    "entry_date": payload.entry_date,
  }

  try:
    return create_transaction_record(transaction_payload)
  except RuntimeError as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc
