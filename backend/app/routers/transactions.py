from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.transactions import TransactionCreate
from app.utils.db import execute, fetch_all
from app.utils.transactions import create_transaction_record

router = APIRouter(tags=["transactions"])


@router.get("/transactions")
def list_transactions(tx_type: Literal["income", "expense"] | None = Query(default=None)) -> list[dict[str, Any]]:
  query = """
    SELECT id, type, amount, category, merchant, source, description, payment_method, status, entry_date, created_at
    FROM transactions
  """
  params: tuple[Any, ...] = ()

  if tx_type:
    query += " WHERE type = %s"
    params = (tx_type,)

  query += " ORDER BY entry_date DESC, created_at DESC"
  return fetch_all(query, params)


@router.post("/transactions", status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate) -> dict[str, Any]:
  try:
    return create_transaction_record(payload.model_dump())
  except RuntimeError as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: str) -> None:
  deleted_rows = execute("DELETE FROM transactions WHERE id = %s", (transaction_id,))
  if deleted_rows == 0:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
